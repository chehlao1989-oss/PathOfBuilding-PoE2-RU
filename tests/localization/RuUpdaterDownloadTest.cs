using System;
using System.IO;
using System.Text;

// Compile with the production updater source, /main:RuUpdaterDownloadTest.
// Fixture URL belongs to this driver, never to the shipped updater CLI.
internal static class RuUpdaterDownloadTest
{
    static int Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        Console.WriteLine("NATIVE_CONSOLE=" + !Console.IsOutputRedirected);
        try
        {
            PoB2RUUpdater.DownloadFile(args[0], args[1]);
            Console.WriteLine("FIXTURE: проверка SHA-256…");
            PoB2RUUpdater.Verify(args[1], args[2]);
            Console.WriteLine("FIXTURE_VERIFIED bytes=" + new FileInfo(args[1]).Length);
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(PoB2RUUpdater.FailureMessage(error));
            return 1;
        }
    }
}
