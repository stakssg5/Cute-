package main

import (
    "flag"
    "fmt"
    "image/png"
    "os"
    "path/filepath"
    "time"
)

func defaultFilename() string {
    return fmt.Sprintf("screenshot_%s.png", time.Now().Format("20060102_150405"))
}

func main() {
    out := flag.String("o", "", "Output PNG path (default: timestamped name in current dir)")
    flag.Parse()

    pngPath := *out
    if pngPath == "" {
        pngPath = defaultFilename()
    }

    if err := os.MkdirAll(filepath.Dir(pngPath), 0o755); err != nil {
        fmt.Fprintf(os.Stderr, "create output dir: %v\n", err)
        os.Exit(2)
    }

    img, err := captureVirtualScreen()
    if err != nil {
        fmt.Fprintf(os.Stderr, "capture failed: %v\n", err)
        os.Exit(3)
    }

    f, err := os.Create(pngPath)
    if err != nil {
        fmt.Fprintf(os.Stderr, "create file: %v\n", err)
        os.Exit(4)
    }
    defer f.Close()

    if err := png.Encode(f, img); err != nil {
        fmt.Fprintf(os.Stderr, "encode png: %v\n", err)
        os.Exit(5)
    }

    b := img.Bounds()
    fmt.Printf("Saved screenshot to %s (%dx%d)\n", pngPath, b.Dx(), b.Dy())
}
