import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins: [react()], clearScreen: false, server: {host:'127.0.0.1',port: 1420, strictPort: true,watch:{ignored:['**/.venv/**','**/tools/**','**/src-tauri/**','**/artifacts/**','**/licenses/**']},proxy:{'/api':'http://127.0.0.1:1419'}}, build: {target: 'es2022',rollupOptions:{output:{manualChunks:{pdf:['pdfjs-dist'],react:['react','react-dom']}}}}});
