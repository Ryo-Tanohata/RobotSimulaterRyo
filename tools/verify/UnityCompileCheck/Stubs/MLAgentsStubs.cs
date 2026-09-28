// ML-Agents 4.x (com.unity.ml-agents) の公開 API のうち、このプロジェクトが使う部分だけを
// 同じ名前空間・同じシグネチャで宣言したスタブ。コンパイル確認専用 (Unity では本物のパッケージを使う)。
using System;
using UnityEngine;

namespace Unity.InferenceEngine
{
    public class ModelAsset : ScriptableObject { }
}

namespace Unity.MLAgents.Actuators
{
    public readonly struct ActionSegment<T> where T : struct
    {
        readonly T[] m_Array;
        public ActionSegment(T[] a) { m_Array = a; }
        public int Length => m_Array.Length;
        public T this[int index] { get => m_Array[index]; set => m_Array[index] = value; }
    }

    public readonly struct ActionBuffers
    {
        public ActionSegment<float> ContinuousActions { get; }
        public ActionBuffers(float[] c) { ContinuousActions = new ActionSegment<float>(c); }
    }

    public struct ActionSpec
    {
        public static ActionSpec MakeContinuous(int numActions) => new ActionSpec();
    }
}

namespace Unity.MLAgents.Sensors
{
    public class VectorSensor
    {
        public void AddObservation(float observation) { }
        public void AddObservation(Vector3 observation) { }
    }
}

namespace Unity.MLAgents.Policies
{
    public enum BehaviorType { Default, HeuristicOnly, InferenceOnly }

    [Serializable]
    public class BrainParameters
    {
        public int VectorObservationSize = 1;
        public int NumStackedVectorObservations = 1;
        public Unity.MLAgents.Actuators.ActionSpec ActionSpec { get; set; }
    }

    public class BehaviorParameters : MonoBehaviour
    {
        public BrainParameters BrainParameters { get; set; } = new BrainParameters();
        public Unity.InferenceEngine.ModelAsset Model { get; set; }
        public BehaviorType BehaviorType { get; set; }
        public string BehaviorName { get; set; }
        public bool UseChildSensors { get; set; }
    }
}

namespace Unity.MLAgents
{
    using Unity.MLAgents.Actuators;
    using Unity.MLAgents.Sensors;

    public class StatsRecorder { public void Add(string key, float value, StatAggregationMethod m = StatAggregationMethod.Average) { } }
    public enum StatAggregationMethod { Average, MostRecent, Sum, Histogram }

    public class Academy
    {
        public static Academy Instance { get; } = new Academy();
        public bool IsCommunicatorOn => false;
        public StatsRecorder StatsRecorder { get; } = new StatsRecorder();
    }

    public class Agent : MonoBehaviour
    {
        [HideInInspector] public int MaxStep;
        public virtual void Initialize() { }
        public virtual void OnEpisodeBegin() { }
        public virtual void CollectObservations(VectorSensor sensor) { }
        public virtual void OnActionReceived(ActionBuffers actions) { }
        public virtual void Heuristic(in ActionBuffers actionsOut) { }
        public void AddReward(float increment) { }
        public void SetReward(float reward) { }
        public float GetCumulativeReward() => 0f;
        public void EndEpisode() { }
        public int StepCount => 0;
    }

    public class DecisionRequester : MonoBehaviour
    {
        public int DecisionPeriod = 5;
        public int DecisionStep = 0;
        public bool TakeActionsBetweenDecisions = true;
    }
}
