import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { from, lastValueFrom } from 'rxjs';

import { Base32 } from '@niyari/base32-ts';

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

  }

  // This method is triggered when a QR/Barcode is detected
  public async onScanSuccess(barcodeData: string): Promise<void> {
    try {
      // 1) Decompress the data (it’s base32-encoded, then Brotli-compressed JSON).
      // const decompressedJson = await this.decompressBrotliData(barcodeData);
      const decompressedJson = barcodeData
      console.log('Decompressed JSON String:', decompressedJson);

      // The decompressed result should be JSON in the format:
      //  {
      //    "d": "<base32-encoded JSON data>",
      //    "s": "<base32-encoded signature>"
      //  }
      const barcodeJson = JSON.parse(decompressedJson);
      console.log('Decompressed JSON:', barcodeJson);

      // Next, decode the 'data' portion (base32 -> string)
      const dataBytes = this.base32Decode(barcodeJson.d);
      const dataStr = new TextDecoder().decode(dataBytes);

      // Decode the signature (base32 -> ArrayBuffer)
      const signature = this.base32Decode(barcodeJson.s).buffer;

      // 3) Verify signature with the public key
      const verified = await this.verifySignature(dataStr, signature);
      if (!verified) {
        this.verificationMessage = '❌ Invalid Signature: Barcode has been tampered with!';
        return;
      }
      this.verificationMessage = '✅ Signature Verified: Barcode is authentic';

      // 4) Check the timestamp
      const barcodeInfo = JSON.parse(dataStr);
      console.log('Barcode Info:', barcodeInfo);
      const currentTimestamp30s = Math.floor(Date.now() / 1000 / 30);
      if (barcodeInfo.t === currentTimestamp30s) {
        this.verificationMessage += '\n✅ Verifying Ticket...';

        this.verifyTicket(barcodeInfo.i);
      } else {
        this.verificationMessage += '\n❌ Expired Barcode';
      }

      // 5) Output ticket info
      this.ticketId = barcodeInfo.i;
    } catch (error) {
      console.error('Error verifying barcode:', error);
      this.verificationMessage = 'Error verifying the barcode.';
    }
  }

  private verifyTicket(ticketId: string): void {
    // Send a POST request to your server to verify the ticket ID

    if (this.ticketId === ticketId) {
      this.verificationMessage = '✅ Ticket is valid';
      return;
    }

    this.http.get<any>('/api/scan-ticket/' + ticketId).subscribe((response) => {
      if (response.success) {
        this.verificationMessage = '✅ Ticket is valid';
      } else {
        this.verificationMessage = '❌ Invalid Ticket';
      }
    });
  }


  /**
   * Converts a base32 encoded string into a Uint8Array.
   */
  private base32Decode(input: string): any {
    const base32 = new Base32({raw: true});
    const output = base32.decode(input);
    return output
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
        saltLength: 32,
      },
      this.publicKey,
      signature,
      dataBuffer
    );
  }
}
