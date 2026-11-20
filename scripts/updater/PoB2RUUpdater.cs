using System;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;
using System.Collections.Generic;

internal static class PoB2RUUpdater
{
    internal const string ProgramName = "Path of Building-PoE2.exe";
    const string Releases = "https://github.com/chehlao1989-oss/PathOfBuilding-PoE2-RU/releases/download/";

    internal static string LongPath(string path)
    {
        string full = Path.GetFullPath(path);
        if (full.StartsWith(@"\\?\")) return full;
        return full.StartsWith(@"\\") ? @"\\?\UNC\" + full.Substring(2) : @"\\?\" + full;
    }

    internal static void Verify(string zip, string expected)
    {
        using (var hash = SHA256.Create())
        using (var file = File.OpenRead(zip))
        {
            var actual = BitConverter.ToString(hash.ComputeHash(file)).Replace("-", "");
            if (!String.Equals(actual, expected, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("SHA-256 скачанного архива не совпадает с данными выпуска.");
        }
    }

    internal static string Unpack(string zip, string stage, string tag)
    {
        stage = LongPath(stage);
        string folder = "PoB2-RU-" + tag.Substring(1);
        using (var archive = ZipFile.OpenRead(zip))
        {
            foreach (var entry in archive.Entries)
            {
                if (!entry.FullName.StartsWith(folder + "/", StringComparison.Ordinal) ||
                    entry.FullName.Contains("\\") || entry.FullName.Contains(":") ||
                    Array.Exists(entry.FullName.Split('/'), part => part == "." || part == ".." ||
                        part.EndsWith(" ") || part.EndsWith(".")))
                    throw new InvalidDataException("Некорректный путь в архиве.");
                string path = Path.Combine(stage, entry.FullName.Replace('/', Path.DirectorySeparatorChar));
                if (entry.Name.Length == 0) Directory.CreateDirectory(path);
                else
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(path));
                    entry.ExtractToFile(path);
                }
            }
        }
        string unpacked = Path.Combine(stage, folder);
        var info = new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(
            File.ReadAllText(Path.Combine(unpacked, "RU-VERSION.json")));
        if (!tag.Equals(info["tag"]) || !File.Exists(Path.Combine(unpacked, ProgramName)))
            throw new InvalidDataException("Версия внутри архива не соответствует выпуску.");
        return unpacked;
    }

    static void CopyData(string source, string target)
    {
        if ((File.GetAttributes(source) & FileAttributes.ReparsePoint) != 0)
            throw new IOException("Нужен ручной перенос ссылки: " + source);
        if (!Directory.Exists(source)) { File.Copy(source, target); return; }
        Directory.CreateDirectory(target);
        foreach (string child in Directory.GetFileSystemEntries(source))
            CopyData(child, Path.Combine(target, Path.GetFileName(child)));
    }

    internal static void Install(string current, string unpacked, string destination)
    {
        foreach (string name in new[] { "Builds", "Settings.xml", "imgui.ini" })
        {
            string source = Path.Combine(current, name);
            if (Directory.Exists(source) || File.Exists(source))
                CopyData(source, Path.Combine(unpacked, name));
        }
        Directory.Move(unpacked, LongPath(destination));
    }

    static void Run(string[] args)
    {
        if (args.Length != 3 || !Regex.IsMatch(args[0], @"\Av\d+\.\d+\.\d+-ru\.\d+(?:-beta\.\d+)?\z") ||
            !Regex.IsMatch(args[1], @"\A[0-9a-f]{64}\z"))
            throw new ArgumentException("Откройте обновление кнопкой в программе PoB.");
        string tag = args[0], folder = "PoB2-RU-" + tag.Substring(1);
        string current = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
        string parent = Directory.GetParent(current).FullName;
        string target = Path.Combine(parent, folder);
        if (Directory.Exists(target)) throw new IOException("Папка уже существует: " + target);
        using (var pob = Process.GetProcessById(Int32.Parse(args[2])))
        {
            if (!String.Equals(pob.MainModule.FileName, Path.Combine(current, ProgramName), StringComparison.OrdinalIgnoreCase))
                throw new IOException("Не удалось определить запущенную копию PoB.");
            // Stage on the destination volume. Only a complete installation is renamed into place.
            string stage = LongPath(Path.Combine(parent, ".pob-ru-" + Guid.NewGuid().ToString("N")));
            Directory.CreateDirectory(stage);
            try
            {
                string name = folder + "-Windows.zip", zip = Path.Combine(stage, name);
                Console.WriteLine("Скачивание русской PoB " + tag + " с GitHub…");
                ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
                using (var client = new WebClient())
                    client.DownloadFile(Releases + tag + "/" + name, zip);
                Verify(zip, args[1]);
                Console.WriteLine("Проверка пройдена. Распаковка…");
                string unpacked = Unpack(zip, stage, tag);
                Console.WriteLine("Сохраните билд и закройте прежнее окно PoB. После этого новая версия откроется автоматически.");
                pob.WaitForExit();
                Install(LongPath(current), unpacked, target);
                Process.Start(new ProcessStartInfo(Path.Combine(target, ProgramName)) { WorkingDirectory = target });
            }
            finally
            {
                Directory.Delete(stage, true);
            }
        }
    }

    static int Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        try
        {
            bool first;
            int pid;
            if (args.Length != 3 || !Int32.TryParse(args[2], out pid))
                throw new ArgumentException("Откройте обновление кнопкой в программе PoB.");
            using (var single = new Mutex(true, @"Local\PoB2RUUpdate-" + pid, out first))
            {
                if (first) Run(args);
            }
            return 0;
        }
        catch (Exception e)
        {
            Console.Error.WriteLine("Обновление остановлено. Ваша прежняя сборка сохранена.\n" + e.Message);
            if (!Console.IsInputRedirected) { Console.WriteLine("Нажмите Enter для выхода."); Console.ReadLine(); }
            return 1;
        }
    }
}
