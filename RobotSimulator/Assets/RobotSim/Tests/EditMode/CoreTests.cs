using System;
using NUnit.Framework;
using RobotSim.Core;

namespace RobotSim.Tests
{
    public class CoreTests
    {
        readonly RobotConfig _c = new RobotConfig();

        [Test]
        public void InverseKinematics_RoundTripsForwardKinematics()
        {
            var rng = new Random(0);
            for (int n = 0; n < 500; n++)
            {
                float side = n % 2 == 0 ? -1f : 1f;
                float hip = (float)(rng.NextDouble() * 0.8 - 0.4);
                float thigh = (float)(rng.NextDouble() * 1.6 - 0.2);
                float calf = (float)(-0.8 - rng.NextDouble() * 1.7);
                Vec3 foot = LegKinematics.Forward(_c, side, hip, thigh, calf);
                LegKinematics.Inverse(_c, side, foot, out float h2, out float t2, out float c2);
                Vec3 again = LegKinematics.Forward(_c, side, h2, t2, c2);
                Assert.Less((again - foot).Magnitude, 1e-3f, $"sample {n}: {foot} -> {again}");
                Assert.AreEqual(hip, h2, 1e-3f);
                Assert.AreEqual(thigh, t2, 1e-3f);
                Assert.AreEqual(calf, c2, 1e-3f);
            }
        }

        [Test]
        public void DefaultPose_FeetAreBelowHipsAtStandingHeight()
        {
            for (int leg = 0; leg < 4; leg++)
            {
                Vec3 foot = LegKinematics.Forward(_c, RobotConfig.SideSign(leg), _c.DefaultHip, _c.DefaultThigh, _c.DefaultCalf);
                Assert.Greater(-foot.y, 0.25f);         // 股関節の 25cm 以上下
                Assert.Less(Math.Abs(foot.z), 0.05f);   // ほぼ真下
                Assert.AreEqual(RobotConfig.SideSign(leg) * _c.HipLinkLength, foot.x, 1e-4f);
            }
            // スポーン高さは足が地面から少し浮く程度
            float standing = -LegKinematics.Forward(_c, 1f, 0f, _c.DefaultThigh, _c.DefaultCalf).y + _c.FootRadius;
            Assert.Greater(_c.SpawnHeight, standing);
            Assert.Less(_c.SpawnHeight - standing, 0.08f);
        }

        [Test]
        public void TrotGait_DiagonalLegsMoveTogetherAndStayInLimits()
        {
            var gait = new TrotGait(_c);
            var q = new float[RobotConfig.JointCount];
            var level = new Vec3(0f, -1f, 0f);
            for (int step = 0; step < 200; step++)
            {
                gait.Step(0.02f, 0.8f, 0.2f, 0.5f, level, q);
                for (int j = 0; j < RobotConfig.JointCount; j++)
                {
                    _c.JointLimits(j, out float lo, out float hi);
                    Assert.That(q[j], Is.InRange(lo, hi));
                    Assert.IsFalse(float.IsNaN(q[j]));
                }
            }
            // その場足踏み: FL と RR は同じ位相 → すね角が同じ (前後の高さの差をなくして比較)
            gait.Reset();
            gait.BodyPitch = 0f;
            gait.Step(0.02f, 0f, 0f, 0f, level, q);
            Assert.AreEqual(q[0 * 3 + 2], q[3 * 3 + 2], 1e-4f);
            Assert.AreEqual(q[1 * 3 + 2], q[2 * 3 + 2], 1e-4f);
        }

        [Test]
        public void TrotGait_StanceFootMovesBackwardWhenWalkingForward()
        {
            var gait = new TrotGait(_c);
            var q = new float[RobotConfig.JointCount];
            var level = new Vec3(0f, -1f, 0f);
            gait.Step(0.01f, 1.0f, 0f, 0f, level, q);  // FL は立脚の初め
            float z0 = LegKinematics.Forward(_c, -1f, q[0], q[1], q[2]).z;
            gait.Step(0.05f, 1.0f, 0f, 0f, level, q);
            float z1 = LegKinematics.Forward(_c, -1f, q[0], q[1], q[2]).z;
            Assert.Less(z1, z0);
        }

        [Test]
        public void Terrain_StairsHaveExpectedStepHeightAndFlatPlatform()
        {
            var gen = new TerrainGenerator { Levels = 5 };
            var tiles = gen.Generate();
            int col = Array.IndexOf(TerrainGenerator.Types, TerrainType.StairsUp);
            var hardest = tiles[col, 4];
            float stepHeight = 0.05f + 0.15f;

            // 端は高さ 0、中央は一番低い
            Assert.AreEqual(0f, hardest.Heights[0, hardest.Cells / 2], 1e-5f);
            float center = hardest.HeightAtLocal(0f, 0f);
            Assert.Less(center, -1f);
            // 段差の大きさはすべて 0 か stepHeight
            for (int i = 0; i < hardest.Cells - 1; i++)
            {
                float d = Math.Abs(hardest.Heights[i + 1, hardest.Cells / 2] - hardest.Heights[i, hardest.Cells / 2]);
                Assert.That(d < 1e-4f || Math.Abs(d - stepHeight) < 1e-4f, $"step {i}: {d}");
            }
            // スタート台は平ら
            Assert.AreEqual(center, hardest.HeightAtLocal(0.9f, -0.9f), 1e-5f);
            Assert.IsTrue(hardest.Blocky);
        }

        [Test]
        public void Terrain_EasiestLevelIsGentle()
        {
            var tiles = new TerrainGenerator { Levels = 5 }.Generate();
            for (int col = 0; col < TerrainGenerator.Types.Length; col++)
            {
                var t = tiles[col, 0];
                float maxJump = 0f;
                for (int i = 0; i < t.Cells - 1; i++)
                    for (int k = 0; k < t.Cells; k++)
                        maxJump = Math.Max(maxJump, Math.Abs(t.Heights[i + 1, k] - t.Heights[i, k]));
                Assert.LessOrEqual(maxJump, 0.101f, t.Type.ToString());
            }
        }

        [Test]
        public void Reward_IsHigherWhenTrackingCommand()
        {
            var cmd = new VelocityCommand(0.8f, 0f, 0f);
            float Eval(float vz)
            {
                var r = new LocomotionReward();
                var s = new RobotState { ProjectedGravity = new Vec3(0, -1, 0), LinearVelocity = new Vec3(0, 0, vz) };
                var zeros = new float[RobotConfig.JointCount];
                return r.Compute(s, cmd, zeros, zeros, zeros, 0.02f);
            }
            Assert.Greater(Eval(0.8f), Eval(0.0f));
            Assert.Greater(Eval(0.8f), Eval(-0.5f));
            Assert.AreEqual((1.0f + 0.5f) * 0.02f, Eval(0.8f), 1e-5f);
        }

        [Test]
        public void Reward_PenalizesBodyCollisions()
        {
            var cmd = new VelocityCommand(0f, 0f, 0f);
            var zeros = new float[RobotConfig.JointCount];
            var ok = new RobotState { ProjectedGravity = new Vec3(0, -1, 0) };
            var hit = new RobotState { ProjectedGravity = new Vec3(0, -1, 0), BodyCollisions = 2 };
            Assert.Greater(new LocomotionReward().Compute(ok, cmd, zeros, zeros, zeros, 0.02f),
                new LocomotionReward().Compute(hit, cmd, zeros, zeros, zeros, 0.02f));
        }

        [Test]
        public void Observation_HasExpectedLayout()
        {
            Assert.AreEqual(45, Observation.Size);
            var s = new RobotState { ProjectedGravity = new Vec3(0, -1, 0) };
            var q0 = _c.DefaultJointAngles();
            Array.Copy(q0, s.JointPositions, q0.Length);
            var obs = new float[Observation.Size];
            Observation.Build(s, new VelocityCommand(0.5f, 0f, 0f), q0, new float[12], obs);
            Assert.AreEqual(-1f, obs[4]);
            Assert.AreEqual(1.0f, obs[6], 1e-6f);
            for (int i = 9; i < 21; i++) Assert.AreEqual(0f, obs[i]); // 基準姿勢なら関節オフセット 0
        }

        [Test]
        public void Curriculum_PromotesAndDemotes()
        {
            var rng = new Random(0);
            Assert.AreEqual(3, TerrainCurriculum.NextLevel(2, 5, 5f, 10f, 8f, rng));
            Assert.AreEqual(1, TerrainCurriculum.NextLevel(2, 5, 1f, 10f, 8f, rng));
            Assert.AreEqual(2, TerrainCurriculum.NextLevel(2, 5, 3f, 5f, 8f, rng));
            int wrapped = TerrainCurriculum.NextLevel(5, 5, 6f, 10f, 8f, rng);
            Assert.That(wrapped, Is.InRange(0, 5));
        }
    }
}
