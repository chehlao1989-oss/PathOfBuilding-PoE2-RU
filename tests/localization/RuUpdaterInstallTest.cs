using System;
using System.IO;
using System.IO.Compression;

// Compile together with scripts/updater/PoB2RUUpdater.cs and select this Main.
internal static class RuUpdaterInstallTest
{
    static void Main(string[] args)
    {
        string root = Path.Combine(Path.GetTempPath(), "PoB RU тест " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            string current = Path.Combine(root, "Прежняя сборка"), target = Path.Combine(root, "Новая сборка");
            Directory.CreateDirectory(Path.Combine(current, "Builds", "Ведьма"));
            string build = Path.Combine("Builds", "Ведьма", "Тест.xml");
            File.WriteAllText(Path.Combine(current, build), "<Build/>");
            File.WriteAllText(Path.Combine(current, "Settings.xml"), "<Settings/>");
            bool rejected = false;
            try { PoB2RUUpdater.Verify(args[0], new string('0', 64)); }
            catch (InvalidDataException) { rejected = true; }
            if (!rejected) throw new Exception("Invalid digest accepted");
            PoB2RUUpdater.Verify(args[0], args[1]);
            string payload = PoB2RUUpdater.Unpack(args[0], Path.Combine(root, "staging"), args[2]);
            Directory.CreateDirectory(target);
            try { PoB2RUUpdater.Install(current, payload, target); throw new Exception("Target replaced"); }
            catch (IOException) {}
            Directory.Delete(target);
            // Retry from a fresh staging area as the production updater does.
            Directory.Delete(payload, true);
            payload = PoB2RUUpdater.Unpack(args[0], Path.Combine(root, "retry"), args[2]);
            PoB2RUUpdater.Install(current, payload, target);
            foreach (var dir in new[] {current, target})
            {
                if (File.ReadAllText(Path.Combine(dir, build)) != "<Build/>" ||
                    File.ReadAllText(Path.Combine(dir, "Settings.xml")) != "<Settings/>")
                    throw new Exception("User data changed");
            }
            if (!File.Exists(Path.Combine(target, PoB2RUUpdater.ProgramName))) throw new Exception("Missing application");
            Console.WriteLine("Hash, extraction, collision, retry and portable migration passed.");
        }
        finally { Directory.Delete(PoB2RUUpdater.LongPath(root), true); }
    }
}
