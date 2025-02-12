import { defineConfig } from 'vite';
import angular from '@analogjs/vite-plugin-angular';
import { viteStaticCopy } from 'vite-plugin-static-copy';

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    mainFields: ['module'],
  },
  root: 'dist/scanner/browser',

  server: {
    proxy: {
      '/api': 'http://localhost:5000'
    },
    host: '0.0.0.0',
    https: {
      
    }
  },

  plugins: [
    angular(),
    viteStaticCopy({
      targets: [
        {
          src: '../../../node_modules/brotli-wasm/pkg.web/brotli_wasm_bg.wasm',
          dest: '' // copy to root of dist or a subdirectory
        }
      ]
    })
  ],
  

});