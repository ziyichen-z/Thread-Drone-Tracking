using System.IO;
using UnityEngine;

namespace TetheredTracking
{
    public static class RuntimePaths
    {
        public static string ProjectRoot =>
            Path.GetFullPath(Path.Combine(Application.dataPath, ".."));

        public static string Root
        {
            get
            {
                string path = Path.Combine(ProjectRoot, "runtime");
                Directory.CreateDirectory(path);
                return path;
            }
        }

        public static string File(string name) => Path.Combine(Root, name);

        public static string ProjectFile(params string[] segments)
        {
            string path = ProjectRoot;
            foreach (string segment in segments) path = Path.Combine(path, segment);
            return path;
        }
    }
}
