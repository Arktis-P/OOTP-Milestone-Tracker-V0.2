using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;

internal static class CardPreviewLauncher
{
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int MessageBox(IntPtr hWnd, string text, string caption, uint type);

    [STAThread]
    private static void Main()
    {
        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string batchPath = Path.Combine(baseDir, "open-card-preview.bat");

        if (!File.Exists(batchPath))
        {
            MessageBox(IntPtr.Zero,
                "open-card-preview.bat was not found next to the launcher.",
                "TEAM YUKIES Card Preview",
                0x10);
            return;
        }

        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = batchPath,
                WorkingDirectory = baseDir,
                UseShellExecute = true
            });
        }
        catch (Exception ex)
        {
            MessageBox(IntPtr.Zero,
                "Unable to start the card preview.\n\n" + ex.Message,
                "TEAM YUKIES Card Preview",
                0x10);
        }
    }
}
