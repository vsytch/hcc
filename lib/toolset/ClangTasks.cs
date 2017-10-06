using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.Build.Framework;

namespace ClangTasks
{
    public class ClangCompile : ITask
    {
        private IBuildEngine engine;
        public IBuildEngine BuildEngine
        {
            get { return engine; }
            set { engine = value; }
        }

        private ITaskHost host;
        public ITaskHost HostObject
        {
            get { return host; }
            set { host = value; }
        }

        private string _verbose;
        public string ClangVerbose
        {
            get { return _verbose; }
            set { _verbose = value; }
        }

        private string _additionaloptions;
        public string ClangAdditionalOptions
        {
            get { return _additionaloptions; }
            set { _additionaloptions = value; }
        }

        private string _additionalincludedirectories;
        public string ClangAdditionalIncludeDirectories
        {
            get { return _additionalincludedirectories; }
            set { _additionalincludedirectories = value; }
        }

        private string _preprocessordefinitions;
        public string ClangPreprocessorDefinitions
        {
            get { return _preprocessordefinitions; }
            set { _preprocessordefinitions = value; }
        }

        private string _vssetup;
        public string ClangVSSetup
        {
            get { return _vssetup; }
            set { _vssetup = value; }
        }

        private string _clang;
        public string Clang
        {
            get { return _clang; }
            set { _clang = value; }
        }

        private string _outputdir;
        public string ClangOutputDir
        {
            get { return _outputdir; }
            set { _outputdir = value; }
        }

        private string _inputs;
        [Required]
        public string ClangInputs
        {
            get { return _inputs; }
            set { _inputs = value; }
        }

        private string _outputs;
        [Required]
        public string ClangOutputs
        {
            get { return _outputs; }
            set { _outputs = value; }
        }

        private static Semaphore _pool;
        private Object _lock;

        private void Compile(string Input, string Output)
        {
            _pool.WaitOne();

            BuildMessageEventArgs Msg;
            Process Compiler = new Process();
            ProcessStartInfo StartInfo = new ProcessStartInfo();
            StartInfo.UseShellExecute = false;
            StartInfo.CreateNoWindow = true;
            StartInfo.RedirectStandardError = true;
            StartInfo.FileName = "cmd.exe";
            StartInfo.Arguments = "/c" + " \"" + _vssetup + " & " + _clang + " -c " + _preprocessordefinitions + " " + _additionaloptions + " " + _additionalincludedirectories + " -o " + "\"" + _outputdir + Output + "\"" + " " + "\"" + Input + "\"" +"\"";

            lock (_lock)
            {
                Msg = new BuildMessageEventArgs("Building " + Output, string.Empty, "ClangTasks", MessageImportance.High);
                engine.LogMessageEvent(Msg);

                if (!string.IsNullOrEmpty(_verbose))
                {
                    Msg = new BuildMessageEventArgs(StartInfo.Arguments + "\r\n\r\n", string.Empty, "ClangTasks", MessageImportance.High);
                    engine.LogMessageEvent(Msg);
                }
            }

            Compiler.StartInfo = StartInfo;
            Compiler.Start();
            string error = Compiler.StandardError.ReadToEnd();
            Compiler.WaitForExit();

            if (!string.IsNullOrEmpty(error))
            {
                lock (_lock)
                {
                    Msg = new BuildMessageEventArgs("\r\n\r\n" + error, string.Empty, "ClangTasks", MessageImportance.High);
                    engine.LogMessageEvent(Msg);
                }
            }

            _pool.Release();
        }

        private void CreateJobs(int NumberOfJobs, string[] InputsList, string[] OutputsList)
        {
            Thread[] CompileJobs = new Thread[NumberOfJobs];

            for (int i = 0; i < NumberOfJobs; i++)
            {
                int k = i;
                CompileJobs[i] = new Thread(() => Compile(InputsList[k], OutputsList[k]));
                CompileJobs[i].Start();
            }

            foreach (Thread thread in CompileJobs)
                thread.Join();
        }

        public bool Execute()
        {
            string[] InputsList = _inputs.Split(new string[] { ";" }, StringSplitOptions.None);
            string[] OutputsList = _outputs.Split(new string[] { ";" }, StringSplitOptions.None);

            _pool = new Semaphore(12, 12);
            _lock = new Object();

            CreateJobs(InputsList.Length, InputsList, OutputsList);

            return true;
        }
    }

    public class ClangLink : ITask
    {
        private IBuildEngine engine;
        public IBuildEngine BuildEngine
        {
            get { return engine; }
            set { engine = value; }
        }

        private ITaskHost host;
        public ITaskHost HostObject
        {
            get { return host; }
            set { host = value; }
        }

        private string _verbose;
        public string ClangVerbose
        {
            get { return _verbose; }
            set { _verbose = value; }
        }

        private string _vssetup;
        public string ClangVSSetup
        {
            get { return _vssetup; }
            set { _vssetup = value; }
        }

        private string _inputs;
        [Required]
        public string ClangInputs
        {
            get { return _inputs; }
            set { _inputs = value; }
        }

        private string _outputs;
        [Required]
        public string ClangOutputs
        {
            get { return _outputs; }
            set { _outputs = value; }
        }

        private string _additionaloptions;
        public string ClangAdditionalOptions
        {
            get { return _additionaloptions; }
            set { _additionaloptions = value; }
        }

        private string _additionaldependencies;
        public string ClangAdditionalDependencies
        {
            get { return _additionaldependencies; }
            set { _additionaldependencies = value; }
        }

        private string _additionallibrarydirectories;
        public string ClangAdditionalLibraryDirectories
        {
            get { return _additionallibrarydirectories; }
            set { _additionallibrarydirectories = value; }
        }

        private string _defaultlibrary;
        public string ClangDefaultLibrary
        {
            get { return _defaultlibrary;  }
            set { _defaultlibrary = value; }
        }

        private string _configuration;
        public string ClangConfiguration
        {
            get { return _configuration; }
            set { _configuration = value; }
        }

        public bool Execute()
        {
            BuildMessageEventArgs Msg;

            Process Linker = new Process();
            ProcessStartInfo StartInfo = new ProcessStartInfo();
            StartInfo.UseShellExecute = false;
            StartInfo.CreateNoWindow = true;
            StartInfo.RedirectStandardError = true;
            StartInfo.FileName = "cmd.exe";
            String Arguments = "/c" + " \"" + _vssetup + " & ";

            if (_configuration == "DynamicLibrary")
            {
                Msg = new BuildMessageEventArgs("Creating shared library " + _outputs, string.Empty, "ClangTasks", MessageImportance.High);
                engine.LogMessageEvent(Msg);

                _additionaloptions += " -Wl,/dll,/subsystem:windows,/machine:x64";
                Arguments += "clang++ " + _additionaloptions + " " + _additionallibrarydirectories + " " + _additionaldependencies + " " + _defaultlibrary + " -o " + "\"" + _outputs + "\"" + " " + "\"" + _inputs + "\"" + "\"";
            }
            else if (_configuration == "StaticLibrary")
            {
                Msg = new BuildMessageEventArgs("Creating static library " + _outputs, string.Empty, "ClangTasks", MessageImportance.High);
                engine.LogMessageEvent(Msg);
            }
            else if (_configuration == "Application")
            {
                Msg = new BuildMessageEventArgs("Linking " + _outputs, string.Empty, "ClangTasks", MessageImportance.High);
                engine.LogMessageEvent(Msg);

                Arguments += "clang++ " + _additionaloptions + " " + _additionaldependencies + " " + _additionallibrarydirectories + " " + _defaultlibrary + " -o " + "\"" + _outputs + "\"" + " " + "\"" + _inputs + "\"" + "\"";
            }

            StartInfo.Arguments = Arguments;

            if (!string.IsNullOrEmpty(_verbose))
            {
                Msg = new BuildMessageEventArgs(StartInfo.Arguments + "\r\n\r\n", string.Empty, "ClangTasks", MessageImportance.High);
                engine.LogMessageEvent(Msg);
            }

            Linker.StartInfo = StartInfo;
            Linker.Start();
            string error = Linker.StandardError.ReadToEnd();
            Linker.WaitForExit();

            if (!string.IsNullOrEmpty(error))
            {
                Msg = new BuildMessageEventArgs("\r\n\r\n" + error, string.Empty, "ClangTasks", MessageImportance.High);
                engine.LogMessageEvent(Msg);
            }

            return true;
        }
    }
}
