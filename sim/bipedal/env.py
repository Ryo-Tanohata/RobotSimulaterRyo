"""学習の環境: 形のつまみ s の体で、前へ進むことを学ぶ (MuJoCo Playground / MJX)。

評価 (報酬) に「2 足で歩け」「手を着け」は入れない:
- 前へ進む速さが目標 (target_speed) に近いほど良い
- エネルギー Σ|関節の力 × 角速度| は少ないほど良い
- 胴体や頭が地面近くまで落ちたら終了 (転倒)
hands_off=True にすると、手が地面に触れたら終了する (実験 C の「2 足のみ」)。
"""
from typing import Any

import jax
import jax.numpy as jp
import mujoco
import numpy as np
from ml_collections import config_dict
from mujoco import mjx
from mujoco_playground._src import mjx_env

from body import actuated_joints, model_xml
from reference import make


def default_config():
    return config_dict.create(
        ctrl_dt=0.02, sim_dt=0.004, episode_length=1000, action_repeat=1, vision=False,
        impl="warp", naconmax=100_000, njmax=160,
        s=1.0, target_speed=1.0, hands_off=False,
        action_scale=0.6, energy_weight=0.0015, alive=0.2, fall_penalty=1.0,
        torque_weight=0.0,
        exp2=False,  # 実験 2: お手本の周期と姿勢を体に合わせる + 足首のばね (reference.make の scaled、body の tendon)  # 支える力の分の減点 (Σ 力^2 × torque_weight)。筋肉は止まっていても力を出すと疲れるため
        # お手本 (reference.py) を土台にする: 目標角 = お手本 + 脳の出力 × residual_scale。お手本との近さも評価に入れる
        imitate=False, residual_scale=0.3, imit_weight=1.0, gait="biped",  # gait: "biped" (2 足) / "quad" (4 足、ナックルウォーク)
    )


def _lowest(m, d, g):
    """形 g の一番低い点の高さ (箱は回転を考える)"""
    if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_BOX:
        return d.geom_xpos[g][2] - np.abs(d.geom_xmat[g].reshape(3, 3)[2]) @ m.geom_size[g]
    return d.geom_xpos[g][2] - m.geom_size[g][0]


class ApeWalk(mjx_env.MjxEnv):
    def __init__(self, config=None, config_overrides=None):
        super().__init__(config or default_config(), config_overrides)
        c = self._config
        xml = model_xml([(c.s, "", (0, 0, 1.5))], tendon=c.exp2)
        self._xml = xml
        self._mj_model = mujoco.MjModel.from_xml_string(xml)
        self._mj_model.opt.timestep = self.sim_dt
        m = self._mj_model
        # 立った姿勢 (関節は範囲の中で 0 に一番近い角度) と、足の裏が床に着く高さ
        d = mujoco.MjData(m)
        for j in range(1, m.njnt):
            lo, hi = m.jnt_range[j]
            d.qpos[m.jnt_qposadr[j]] = np.clip(0, lo, hi)
        mujoco.mj_forward(m, d)
        feet = [m.geom(f"{s}_foot").id for s in "lr"]
        d.qpos[2] -= min(d.geom_xpos[k][2] - m.geom_size[k][2] for k in feet) - 0.005
        self._ref, self._freq, pitch = make(c.gait, c.s, scaled=c.exp2)
        if c.imitate and pitch:
            # 4 足: 胴体を前へ倒し、お手本のどの瞬間でも手足が床に埋まらない高さから始める
            th = np.radians(pitch) / 2
            d.qpos[3:7] = (np.cos(th), 0, np.sin(th), 0)
            jids = [m.joint(n).id for n in actuated_joints()]
            contacts = [m.geom(f"{x}_{y}").id for x in "lr" for y in ("foot", "hand")]
            need = []
            for ph in np.linspace(0, 1, 24, endpoint=False):
                d.qpos[m.jnt_qposadr[jids]] = np.clip(np.array(self._ref(ph)), m.jnt_range[jids, 0], m.jnt_range[jids, 1])
                d.qpos[2] = 1.0
                mujoco.mj_forward(m, d)
                need.append(min(_lowest(m, d, g) for g in contacts))
            d.qpos[2] = 1.0 - min(need) + 0.01
        self._qpos0 = jp.array(d.qpos)
        self._joint_ids = np.array([m.joint(n).id for n in actuated_joints()])
        self._qadr = jp.array(m.jnt_qposadr[self._joint_ids])
        self._vadr = jp.array(m.jnt_dofadr[self._joint_ids])
        self._lo = jp.array(m.jnt_range[self._joint_ids, 0])
        self._hi = jp.array(m.jnt_range[self._joint_ids, 1])
        self._default = self._qpos0[self._qadr]
        self._pelvis = m.body("pelvis").id
        self._head = m.body("head").id
        self._hands = jp.array([m.geom(f"{s}_hand").id for s in "lr"])
        self._hand_r = float(m.geom_size[m.geom("l_hand").id][0])
        self._mjx_model = mjx.put_model(m, impl=c.impl)

    # ---- Playground が必要とするもの ----
    @property
    def xml_path(self):
        return ""

    @property
    def action_size(self):
        return len(self._joint_ids)

    @property
    def mj_model(self):
        return self._mj_model

    @property
    def mjx_model(self):
        return self._mjx_model

    def reset(self, rng):
        rng, k1, k2, k3 = jax.random.split(rng, 4)
        phase = jax.random.uniform(k3)
        qpos0 = self._qpos0.at[self._qadr].set(jp.clip(self._ref(phase), self._lo, self._hi)) if self._config.imitate else self._qpos0
        qpos = qpos0.at[self._qadr].add(jax.random.uniform(k1, (self.action_size,), minval=-0.05, maxval=0.05))
        qvel = jp.zeros(self._mj_model.nv).at[:6].set(jax.random.uniform(k2, (6,), minval=-0.1, maxval=0.1))
        data = mjx_env.make_data(self._mj_model, qpos=qpos, qvel=qvel, ctrl=self._default,
                                 impl=self._mjx_model.impl.value, naconmax=self._config.naconmax, njmax=self._config.njmax)
        data = mjx.forward(self._mjx_model, data)
        info = {"rng": rng, "last_act": jp.zeros(self.action_size), "phase": phase}
        metrics = {k: jp.zeros(()) for k in ("speed", "energy", "torque", "biped", "reward/forward", "reward/energy", "reward/imitate")}
        obs = self._obs(data, info)
        return mjx_env.State(data, obs, jp.zeros(()), jp.zeros(()), metrics, info)

    def step(self, state, action):
        c = self._config
        phase = (state.info["phase"] + self._freq * self.dt) % 1.0
        ref = self._ref(phase)
        if c.imitate:
            target = jp.clip(ref + action * c.residual_scale, self._lo, self._hi)
        else:
            target = jp.clip(self._default + action * c.action_scale, self._lo, self._hi)
        data = mjx_env.step(self._mjx_model, state.data, target, self.n_substeps)

        vx = data.qvel[0]
        power = jp.sum(jp.abs(data.actuator_force * data.qvel[self._vadr]))
        hands_z = data.geom_xpos[self._hands, 2]
        hands_up = jp.all(hands_z > self._hand_r + 0.02)
        forward = jp.exp(-jp.square(vx - c.target_speed) / 0.25)
        torque = jp.sum(jp.abs(data.actuator_force))
        energy = -c.energy_weight * power - c.torque_weight * jp.sum(jp.square(data.actuator_force))
        q_err = jp.mean(jp.square(data.qpos[self._qadr] - ref))
        imit = jp.exp(-8.0 * q_err) * c.imit_weight if c.imitate else jp.zeros(())
        reward = forward + energy + c.alive + imit

        fell = (data.xpos[self._pelvis, 2] < 0.2) | (data.xpos[self._head, 2] < 0.25)
        bad = jp.isnan(data.qpos).any() | jp.isnan(data.qvel).any()
        done = fell | bad
        if c.hands_off:
            done = done | ~hands_up
        reward = jp.where(done, -c.fall_penalty, reward)
        state.info["phase"] = phase

        state.info["last_act"] = action
        m = state.metrics
        m.update(speed=vx, energy=power, torque=torque, biped=hands_up.astype(float), **{"reward/forward": forward, "reward/energy": energy, "reward/imitate": imit})
        obs = self._obs(data, state.info)
        return state.replace(data=data, obs=obs, reward=reward, done=done.astype(float), metrics=m)

    def _obs(self, data, info: dict[str, Any]):
        rot = data.xmat[self._pelvis]  # 骨盤の向き (世界 → 体)
        gravity = rot.T @ jp.array([0.0, 0.0, -1.0])
        linvel = rot.T @ data.qvel[:3]
        angvel = rot.T @ data.qvel[3:6]
        return jp.concatenate([
            gravity, linvel, angvel, data.xpos[self._pelvis, 2:3],
            data.qpos[self._qadr] - self._default, data.qvel[self._vadr] * 0.1, info["last_act"],
        ] + ([jp.stack([jp.sin(2 * jp.pi * info["phase"]), jp.cos(2 * jp.pi * info["phase"])])] if self._config.imitate else []))
