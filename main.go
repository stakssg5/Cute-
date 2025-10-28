package main

import (
	"flag"
	"fmt"
	"image"
	"image/draw"
	"image/png"
	"os"
	"path/filepath"
	"time"

	"github.com/kbinani/screenshot"
)

func defaultFilename() string {
	return fmt.Sprintf("screenshot_%s.png", time.Now().Format("20060102_150405"))
}

func captureAllMonitors() (image.Image, error) {
	n := screenshot.NumActiveDisplays()
	if n <= 0 {
		return nil, fmt.Errorf("no active displays detected")
	}

	// Compute virtual bounds spanning all monitors
	bounds := image.Rect(0, 0, 0, 0)
	for i := 0; i < n; i++ {
		b := screenshot.GetDisplayBounds(i)
		bounds = bounds.Union(b)
	}

	img := image.NewRGBA(bounds)
	for i := 0; i < n; i++ {
		b := screenshot.GetDisplayBounds(i)
		shot, err := screenshot.CaptureRect(b)
		if err != nil {
			return nil, fmt.Errorf("capture display %d: %w", i, err)
		}
		draw.Draw(img, b, shot, b.Min, draw.Src)
	}
	return img, nil
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

	img, err := captureAllMonitors()
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

	fmt.Printf("Saved screenshot to %s (%dx%d)\n", pngPath, img.Bounds().Dx(), img.Bounds().Dy())
}
