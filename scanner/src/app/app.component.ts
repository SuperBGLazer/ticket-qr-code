import { Component } from '@angular/core';
import { BarcodeScannerComponent } from "./barcode-scanner/barcode-scanner.component";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  title = 'scanner';
}
