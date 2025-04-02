package util

import (
	"crypto/rand"
	"fmt"
	qrcode "github.com/skip2/go-qrcode"
)

func generateRandomString(n int) string {
	const letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

	bytes := make([]byte, n)
	_, err := rand.Read(bytes)
	if err != nil {
		panic(err) // handle this properly in production
	}

	for i := 0; i < n; i++ {
		bytes[i] = letters[bytes[i]%byte(len(letters))]
	}

	return string(bytes)
}

// Create .h file
func createHeaderFile(hex string) string {
	content := "#define QRCODE_HEIGHT 240\n#define QRCODE_WIDTH 240\n"
	content += "static const unsigned char qr[] PROGMEM = {\n"

	content += hex
	content += "\n};"
	return content
}

func GenerateQRhexCode() (string, error) {

	var png []byte
	png, err := qrcode.Encode(generateRandomString(16), qrcode.Medium, 240)
	if err != nil {
		return "-1", err
	}

	qr_hex := ""
	for i, b := range png {
		qr_hex += fmt.Sprintf("0x%02x", b)
		if i < len(png)-1 {
			qr_hex += ", "
		}
	}

	hex_image_header := createHeaderFile(qr_hex)
	return hex_image_header, nil
}
