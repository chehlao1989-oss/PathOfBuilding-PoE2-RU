using System;
using System.Diagnostics;
using System.Globalization;
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

    internal sealed class DownloadProgress : IDisposable
    {
        readonly TextWriter output;
        readonly bool inline;
        readonly Stopwatch timer = Stopwatch.StartNew();
        long lastMilliseconds = -1000, lastReceived = -1, lastTotal = Int64.MinValue;
        int lastWidth;
        bool lineOpen;

        internal DownloadProgress(TextWriter output, bool inline)
        {
            this.output = output;
            this.inline = inline;
        }

        internal static string Size(long bytes)
        {
            var culture = CultureInfo.GetCultureInfo("ru-RU");
            if (bytes < 1024) return bytes.ToString(culture) + " байт";
            if (bytes < 1024 * 1024) return (bytes / 1024.0).ToString("F1", culture) + " КиБ";
            return (bytes / (1024.0 * 1024)).ToString("F1", culture) + " МиБ";
        }

        internal void Report(long received, long total, bool final)
        {
            long now = timer.ElapsedMilliseconds;
            if (!final && total == lastTotal && now - lastMilliseconds < 1000) return;
            if (received != lastReceived || total != lastTotal)
            {
                string text = "Скачано: " + Size(received);
                if (total > 0)
                    text += " из " + Size(total) + " (" + Math.Min(100.0, received * 100.0 / total)
                        .ToString("F1", CultureInfo.GetCultureInfo("ru-RU")) + "%)";
                else text += " (общий размер неизвестен)";
                if (inline)
                {
                    output.Write("\r" + text + new string(' ', Math.Max(0, lastWidth - text.Length)));
                    lastWidth = text.Length;
                    lineOpen = true;
                }
                else output.WriteLine(text);
                output.Flush();
                lastMilliseconds = now;
                lastReceived = received;
                lastTotal = total;
            }
            if (final) Dispose();
        }

        public void Dispose()
        {
            if (lineOpen) { output.WriteLine(); output.Flush(); lineOpen = false; }
        }
    }

    // The production URL/TLS remain in Run. Tests supply a local fixture stream here.
    internal static long Download(Stream input, string destination, long total, DownloadProgress progress)
    {
        long received = 0;
        progress.Report(0, total, false);
        using (var file = new FileStream(destination, FileMode.Create, FileAccess.Write, FileShare.None))
        {
            var buffer = new byte[65536];
            int count;
            while ((count = input.Read(buffer, 0, buffer.Length)) != 0)
            {
                file.Write(buffer, 0, count);
                received += count;
                if (total > 0 && received > total)
                    throw new InvalidDataException("Получено больше данных, чем объявлено сервером. Архив не будет установлен.");
                progress.Report(received, total, false);
            }
            if (total > 0 && received != total)
                throw new EndOfStreamException("Соединение прервалось: скачано " + DownloadProgress.Size(received)
                    + " из " + DownloadProgress.Size(total) + ". Архив не будет установлен.");
        }
        progress.Report(received, total, true);
        return received;
    }

    internal static void DownloadFile(string url, string destination)
    {
        ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
        using (var client = new WebClient())
        using (var progress = new DownloadProgress(Console.Out, !Console.IsOutputRedirected))
        {
            progress.Report(0, -1, false);
            using (var input = client.OpenRead(url))
            {
                long total;
                if (!Int64.TryParse(client.ResponseHeaders[HttpResponseHeader.ContentLength], NumberStyles.None,
                    CultureInfo.InvariantCulture, out total) || total <= 0) total = -1;
                Download(input, destination, total, progress);
            }
        }
    }

    internal static string FailureMessage(Exception error)
    {
        var launch = error as InstalledCopyLaunchException;
        if (launch != null)
            return "Файлы обновления установлены, но новая PoB не запущена. Прежняя папка сохранена."
                + "\nПричина запуска: " + launch.InnerException.Message
                + "\nЭта попытка установила проверенный архив в: " + launch.Destination
                + "\nЗапустите вручную: " + Path.Combine(launch.Destination, ProgramName);
        var web = error as WebException;
        string reason = error.Message;
        if (web != null)
        {
            var response = web.Response as HttpWebResponse;
            if (response != null) reason = "GitHub вернул HTTP " + (int)response.StatusCode + " (" + response.StatusDescription + ").";
            else if (web.Status == WebExceptionStatus.Timeout) reason = "Истекло время ожидания ответа. Проверьте соединение и повторите загрузку.";
            else if (web.Status == WebExceptionStatus.NameResolutionFailure) reason = "Не удалось определить адрес GitHub. Проверьте соединение с интернетом.";
            else if (web.Status == WebExceptionStatus.ConnectFailure || web.Status == WebExceptionStatus.ReceiveFailure || web.Status == WebExceptionStatus.ConnectionClosed)
                reason = "Соединение с GitHub прервалось или не установлено. Проверьте интернет и повторите загрузку.";
        }
        else
            for (Exception inner = error.InnerException; inner != null; inner = inner.InnerException)
                if (inner is System.Net.Sockets.SocketException)
                {
                    reason = "Сетевое соединение прервалось во время загрузки. Проверьте интернет и повторите загрузку.";
                    break;
                }
        return "Обновление остановлено. Ваша прежняя сборка сохранена.\nПричина: " + reason
            + "\nДля повтора откройте прежнюю PoB: «Обновления» или Ctrl+U → «Обновить PoB». Загрузка начнётся заново.";
    }

    internal sealed class InstalledCopyLaunchException : IOException
    {
        internal readonly string Destination;
        internal InstalledCopyLaunchException(string destination, Exception inner)
            : base("Не удалось запустить установленную копию PoB.", inner) { Destination = destination; }
    }

    // Run calls this only after Install has completed successfully.
    internal static void StartInstalledCopy(string target)
    {
        try
        {
            using (var next = Process.Start(new ProcessStartInfo(Path.Combine(target, ProgramName)) { WorkingDirectory = target }))
                if (next == null) throw new IOException("Windows не создала новый процесс PoB.");
        }
        catch (Exception error) { throw new InstalledCopyLaunchException(target, error); }
    }

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
                DownloadFile(Releases + tag + "/" + name, zip);
                Console.WriteLine("Проверка SHA-256 скачанного архива…");
                Verify(zip, args[1]);
                Console.WriteLine("SHA-256 подтверждён. Проверка и распаковка архива…");
                string unpacked = Unpack(zip, stage, tag);
                Console.WriteLine("Архив подготовлен. Сохраните билд и закройте прежнее окно PoB.\nУстановщик дождётся закрытия; не закрывайте это окно.");
                pob.WaitForExit();
                Console.WriteLine("Перенос билдов и настроек в новую папку…");
                Install(LongPath(current), unpacked, target);
                Console.WriteLine("Перенос завершён. Запуск новой PoB…");
                StartInstalledCopy(target);
            }
            finally
            {
                Directory.Delete(stage, true);
            }
            Console.WriteLine("Готово. Обновление установлено, новая PoB запущена.\nПрежняя папка сохранена. Новая папка: " + target);
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
            Console.Error.WriteLine(FailureMessage(e));
            if (!Console.IsInputRedirected) { Console.WriteLine("Нажмите Enter для выхода."); Console.ReadLine(); }
            return 1;
        }
    }
}
