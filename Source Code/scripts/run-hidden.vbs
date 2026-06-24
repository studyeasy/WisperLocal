' Launch WisperLocal with no console window.
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
proj = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
sh.CurrentDirectory = proj
sh.Run """" & proj & "\.venv\Scripts\pythonw.exe"" -m wisperlocal", 0, False
