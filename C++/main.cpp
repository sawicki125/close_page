#include <windows.h>
#include <cstdio>
int main() {
    // Full path to pythonw.exe
    LPCSTR pythonExe = "C:\\Users\\adam\\AppData\\Local\\Programs\\Python\\Python314\\pythonw.exe";
    
    // Full path to your server.py
    LPCSTR scriptPath = "C:\\close_page\\server.py";

    // Build command line
    CHAR cmdLine[MAX_PATH];
    snprintf(cmdLine, MAX_PATH, "\"%s\" \"%s\"", pythonExe, scriptPath);

    STARTUPINFOA si = { sizeof(si) };
    PROCESS_INFORMATION pi;

    // Hide the window
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;

    if (CreateProcessA(
            NULL,
            cmdLine,
            NULL,
            NULL,
            FALSE,
            0,
            NULL,
            NULL,
            &si,
            &pi
        )) {
        // Close handles since we don't need them
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
    }

    return 0;
}
