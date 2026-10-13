Option Explicit

Dim FSO, WshShell, Folder, ScriptPath
Dim PythonW, PythonExe, Command, Result, ShellExec

Set FSO = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

Folder = FSO.GetParentFolderName(WScript.ScriptFullName)
ScriptPath = FSO.BuildPath(Folder, "note.py")

If Not FSO.FileExists(ScriptPath) Then
    MsgBox "Cannot find note.py in:" & vbCrLf & Folder, vbExclamation, "Desktop Sticky Note"
    WScript.Quit 1
End If

WshShell.CurrentDirectory = Folder
PythonW = ""
PythonExe = ""

On Error Resume Next
Set ShellExec = WshShell.Exec("cmd.exe /c where pyw.exe 2>nul")
Result = ShellExec.StdOut.ReadAll
On Error GoTo 0

If Len(Trim(Result)) > 0 Then
    PythonW = Trim(Split(Replace(Result, vbCr, ""), vbLf)(0))
End If

If PythonW = "" Then
    On Error Resume Next
    Set ShellExec = WshShell.Exec("cmd.exe /c where pythonw.exe 2>nul")
    Result = ShellExec.StdOut.ReadAll
    On Error GoTo 0

    If Len(Trim(Result)) > 0 Then
        PythonExe = Trim(Split(Replace(Result, vbCr, ""), vbLf)(0))
    End If
End If

If PythonW = "" And PythonExe = "" Then
    MsgBox "Python could not be found. Please run Install Sticky Note.bat first.", vbExclamation, "Desktop Sticky Note"
    WScript.Quit 1
End If

If PythonW <> "" Then
    Command = """" & PythonW & """ -3 """ & ScriptPath & """"
Else
    Command = """" & PythonExe & """ """ & ScriptPath & """"
End If

WshShell.Run Command, 0, False

Set ShellExec = Nothing
Set WshShell = Nothing
Set FSO = Nothing