import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ZXingScannerComponent } from '@zxing/ngx-scanner';
import { from, lastValueFrom } from 'rxjs';

// Use the ESM version of Brotli from 'brotli-wasm'
import brotliPromise from 'brotli-wasm';

@Component({
  selector: 'app-barcode-scanner',
  templateUrl: './barcode-scanner.component.html',
  styleUrls: ['./barcode-scanner.component.scss'],
})
export class BarcodeScannerComponent implements OnInit {
  // We will keep track of scanning status
  hasCamera: boolean = false;
  scanResult: string = '';
  verificationMessage: string = '';
  ticketId: string = '';

  // The public key (in SubtleCrypto format) once loaded
  publicKey!: CryptoKey;

  constructor(private http: HttpClient) {}

  async ngOnInit() {
    // 1) Load the public key from your server on initialization
    //    and convert it into a SubtleCrypto key.
    const publicKeyPem = await lastValueFrom(this.http.get('/api/public-key', { responseType: 'text' }));
    this.publicKey = await this.importRsaPssKey(publicKeyPem);

    // 2) Ensure the brotli wasm module is loaded before scanning
    await brotliPromise;
  }

  // This method is triggered when a QR/Barcode is detected
  public async onScanSuccess(barcodeData: string): Promise<void> {
    // Decompress the data (it’s base64-encoded, then Brotli-compressed JSON).
    try {
      const decompressedJson = await this.decompressBrotliData(barcodeData);

      // The decompressed result should be JSON in the format:
      //  {
      //    "data": "<base64-encoded JSON>",
      //    "signature": "<base64-encoded signature>"
      //  }
      const barcodeJson = JSON.parse(decompressedJson);

      // Next, decode the 'data' portion (base64 -> string)
      const dataStr = atob(barcodeJson.data);

      // Decode the signature
      const signature = this.base64ToArrayBuffer(barcodeJson.signature);

      // 3) Verify signature with the public key
      const verified = await this.verifySignature(dataStr, signature);
      if (!verified) {
        this.verificationMessage = '❌ Invalid Signature: Barcode has been tampered with!';
        return;
      }
      this.verificationMessage = '✅ Signature Verified: Barcode is authentic';

      // 4) Check the timestamp
      const barcodeInfo = JSON.parse(dataStr);
      const currentTimestamp30s = Math.floor(Date.now() / 1000 / 30);
      if (barcodeInfo.timestamp === currentTimestamp30s) {
        this.verificationMessage += '\n✅ Barcode is valid for entry';
      } else {
        this.verificationMessage += '\n❌ Expired Barcode';
      }

      // 5) Output ticket info
      this.ticketId = `Ticket ID: ${barcodeInfo.ticket_id}`;
    } catch (error) {
      console.error('Error verifying barcode:', error);
      this.verificationMessage = 'Error verifying the barcode.';
    }
  }

  /**
   * Decompresses the raw base64-encoded, Brotli-compressed string.
   */
  private async decompressBrotliData(base64Compressed: string): Promise<string> {
    // 1) base64 -> Uint8Array
    const compressedBytes = this.base64ToUint8Array(base64Compressed);

    // 2) Decompress via brotli-wasm
    //    Wait for the brotli wasm to be ready
    const brotli = await brotliPromise;
    const decompressedBytes = brotli.decompress(compressedBytes);

    // 3) Convert to string
    return new TextDecoder().decode(decompressedBytes);
  }

  /**
   * Imports the PEM-encoded RSA public key as a SubtleCrypto key using RSA-PSS with SHA-256.
   */
  private async importRsaPssKey(pemKey: string): Promise<CryptoKey> {
    // Remove the PEM header/footer and newlines
    const pemContents = pemKey
      .replace(/-----BEGIN PUBLIC KEY-----/g, '')
      .replace(/-----END PUBLIC KEY-----/g, '')
      .replace(/\s+/g, '');

    const binaryDerString = window.atob(pemContents);
    const len = binaryDerString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryDerString.charCodeAt(i);
    }

    // Import the key (SPKI format)
    return crypto.subtle.importKey(
      'spki',
      bytes.buffer,
      {
        name: 'RSA-PSS',
        hash: { name: 'SHA-256' },
      },
      true,
      ['verify']
    );
  }

  /**
   * Verifies signature with RSA-PSS (SHA-256).
   */
  private async verifySignature(data: string, signature: ArrayBuffer): Promise<boolean> {
    console.log('Verifying signature:', data, signature);
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);

    return crypto.subtle.verify(
      {
        name: 'RSA-PSS',
        saltLength: 32, // adjust if needed (for a 2048-bit key, 32 is typical)
      },
      this.publicKey,
      signature,
      dataBuffer
    );
  }

  /**
   * Helper to convert a base64 string to ArrayBuffer
   */
  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  }

  /**
   * Helper to convert base64 -> Uint8Array
   */
  private base64ToUint8Array(base64: string): Uint8Array {
    return new Uint8Array(this.base64ToArrayBuffer(base64));
  }
}
