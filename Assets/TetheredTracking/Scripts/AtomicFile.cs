using System;
using System.IO;

namespace TetheredTracking
{
    public static class AtomicFile
    {
        public static void WriteAllText(string destination, string contents)
        {
            string temporary = TemporaryPath(destination);
            try
            {
                File.WriteAllText(temporary, contents);
                Publish(temporary, destination);
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
        }

        public static void WriteAllBytes(string destination, byte[] contents)
        {
            string temporary = TemporaryPath(destination);
            try
            {
                File.WriteAllBytes(temporary, contents);
                Publish(temporary, destination);
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
        }

        static string TemporaryPath(string destination)
        {
            string directory = Path.GetDirectoryName(destination);
            if (string.IsNullOrEmpty(directory)) throw new ArgumentException("Destination needs a directory.");
            Directory.CreateDirectory(directory);
            return Path.Combine(directory, "." + Path.GetFileName(destination) + "." + Guid.NewGuid() + ".tmp");
        }

        static void Publish(string temporary, string destination)
        {
            if (File.Exists(destination)) File.Replace(temporary, destination, null);
            else File.Move(temporary, destination);
        }
    }
}
