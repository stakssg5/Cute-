#include <windows.h>
#include <gdiplus.h>
#include <string>
#include <sstream>
#include <iomanip>
#include <ctime>

#pragma comment(lib, "gdiplus.lib")
#pragma comment(lib, "gdi32.lib")

using namespace Gdiplus;

static int GetEncoderClsid(const WCHAR* format, CLSID* pClsid) {
    UINT  num = 0;          // number of image encoders
    UINT  size = 0;         // size of the image encoder array in bytes

    GetImageEncodersSize(&num, &size);
    if (size == 0) return -1;  // Failure

    ImageCodecInfo* pImageCodecInfo = (ImageCodecInfo*)(malloc(size));
    if (pImageCodecInfo == nullptr) return -1;  // Failure

    GetImageEncoders(num, size, pImageCodecInfo);

    for (UINT j = 0; j < num; ++j) {
        if (wcscmp(pImageCodecInfo[j].MimeType, format) == 0 ||
            wcscmp(pImageCodecInfo[j].FormatDescription, L"PNG") == 0) {
            *pClsid = pImageCodecInfo[j].Clsid;
            free(pImageCodecInfo);
            return (int)j;
        }
    }

    free(pImageCodecInfo);
    return -1;  // Failure
}

static std::wstring generateDefaultPath() {
    std::wstringstream ss;
    std::time_t t = std::time(nullptr);
    std::tm tmLocal{};
#ifdef _WIN32
    localtime_s(&tmLocal, &t);
#else
    tmLocal = *std::localtime(&t);
#endif
    ss << L"screenshot_" << std::put_time(&tmLocal, L"%Y%m%d_%H%M%S") << L".png";
    return ss.str();
}

int wmain(int argc, wchar_t* argv[]) {
    // Initialize GDI+
    ULONG_PTR gdiplusToken = 0;
    GdiplusStartupInput gdiplusStartupInput;
    if (GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, nullptr) != Ok) {
        fwprintf(stderr, L"Failed to initialize GDI+\n");
        return 1;
    }

    // Determine virtual screen size (all monitors)
    int x = GetSystemMetrics(SM_XVIRTUALSCREEN);
    int y = GetSystemMetrics(SM_YVIRTUALSCREEN);
    int width = GetSystemMetrics(SM_CXVIRTUALSCREEN);
    int height = GetSystemMetrics(SM_CYVIRTUALSCREEN);
    if (width <= 0 || height <= 0) {
        x = 0; y = 0;
        width = GetSystemMetrics(SM_CXSCREEN);
        height = GetSystemMetrics(SM_CYSCREEN);
    }

    HDC hScreenDC = GetDC(nullptr);
    if (!hScreenDC) {
        fwprintf(stderr, L"Failed to acquire screen DC\n");
        GdiplusShutdown(gdiplusToken);
        return 2;
    }

    HDC hMemDC = CreateCompatibleDC(hScreenDC);
    if (!hMemDC) {
        fwprintf(stderr, L"Failed to create memory DC\n");
        ReleaseDC(nullptr, hScreenDC);
        GdiplusShutdown(gdiplusToken);
        return 3;
    }

    HBITMAP hBitmap = CreateCompatibleBitmap(hScreenDC, width, height);
    if (!hBitmap) {
        fwprintf(stderr, L"Failed to create bitmap\n");
        DeleteDC(hMemDC);
        ReleaseDC(nullptr, hScreenDC);
        GdiplusShutdown(gdiplusToken);
        return 4;
    }

    HGDIOBJ hOld = SelectObject(hMemDC, hBitmap);
    if (!BitBlt(hMemDC, 0, 0, width, height, hScreenDC, x, y, SRCCOPY | CAPTUREBLT)) {
        fwprintf(stderr, L"Failed to capture screen\n");
        SelectObject(hMemDC, hOld);
        DeleteObject(hBitmap);
        DeleteDC(hMemDC);
        ReleaseDC(nullptr, hScreenDC);
        GdiplusShutdown(gdiplusToken);
        return 5;
    }

    SelectObject(hMemDC, hOld);

    std::wstring outPath;
    if (argc >= 2) {
        outPath = argv[1];
    } else {
        outPath = generateDefaultPath();
    }

    CLSID pngClsid{};
    if (GetEncoderClsid(L"image/png", &pngClsid) == -1) {
        fwprintf(stderr, L"PNG encoder not found\n");
        DeleteObject(hBitmap);
        DeleteDC(hMemDC);
        ReleaseDC(nullptr, hScreenDC);
        GdiplusShutdown(gdiplusToken);
        return 6;
    }

    Status saveStatus = GenericError;
    {
        Bitmap bmp(hBitmap, nullptr);
        saveStatus = bmp.Save(outPath.c_str(), &pngClsid, nullptr);
    }

    DeleteObject(hBitmap);
    DeleteDC(hMemDC);
    ReleaseDC(nullptr, hScreenDC);
    GdiplusShutdown(gdiplusToken);

    if (saveStatus != Ok) {
        fwprintf(stderr, L"Failed to save PNG to %ls (status=%d)\n", outPath.c_str(), (int)saveStatus);
        return 7;
    }

    wprintf(L"Saved screenshot to %ls (%dx%d)\n", outPath.c_str(), width, height);
    return 0;
}
