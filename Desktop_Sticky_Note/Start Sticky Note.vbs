
Option Explicit

Dim FSO, WshShell, Folder, ScriptPath, PythonW, Command

Set FSO = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

Folder = FSO.GetParentFolderName(WScript.ScriptFullName)
ScriptPath = FSO.BuildPath(Folder, "note.py")

PythonW = "C:\Users\Riski\AppData\Local\Programs\Python\Python311\pythonw.exe"

If Not FSO.FileExists(ScriptPath) Then
    MsgBox "Cannot find note.py in:" & vbCrLf & Folder, vbExclamation, "Desktop Sticky Note"
    WScript.Quit 1
End If

If Not FSO.FileExists(PythonW) Then
    MsgBox "Cannot find Python 3.11:" & vbCrLf & PythonW, vbExclamation, "Desktop Sticky Note"
    WScript.Quit 1
End If

WshShell.CurrentDirectory = Folder

Command = """" & PythonW & """ """ & ScriptPath & """"
WshShell.Run Command, 0, False

Set WshShell = Nothing
Set FSO = Nothing
