using System.IO;
using System.Text.Json;
using NUnit.Framework;
using RobotSim.Core;

namespace RobotSim.Tests
{
    /// <summary>C# 版 (Unity) と JavaScript 版 (Web) の歩容が同じ関節目標角を出すか確認する。</summary>
    public class ParityTests
    {
        [Test]
        public void TrotGait_MatchesJavaScriptImplementation()
        {
            string path = Path.Combine(TestContext.CurrentContext.TestDirectory, "gait_fixture.json");
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            float dt = doc.RootElement.GetProperty("dt").GetSingle();
            var gait = new TrotGait(new RobotConfig());
            var q = new float[RobotConfig.JointCount];
            int n = 0;
            foreach (var step in doc.RootElement.GetProperty("steps").EnumerateArray())
            {
                var cmd = step.GetProperty("cmd");
                var g = step.GetProperty("gravity");
                gait.Step(dt, cmd[0].GetSingle(), cmd[1].GetSingle(), cmd[2].GetSingle(),
                    new Vec3(g[0].GetSingle(), g[1].GetSingle(), g[2].GetSingle()), q);
                int j = 0;
                foreach (var expected in step.GetProperty("targets").EnumerateArray())
                {
                    Assert.AreEqual(expected.GetSingle(), q[j], 2e-4f, $"step {n} joint {j}");
                    j++;
                }
                n++;
            }
            Assert.AreEqual(120, n);
        }
    }
}
