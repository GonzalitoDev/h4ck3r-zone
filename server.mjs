import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const port = process.env.PORT || 8080;

const gameDir = path.join(__dirname, 'game');

app.use(express.static(gameDir, {
  extensions: ['html'],
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('.html')) {
      res.setHeader('Cache-Control', 'no-cache');
    } else {
      res.setHeader('Cache-Control', 'public, max-age=3600');
    }
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  }
}));

app.use((req, res) => {
  res.sendFile(path.join(gameDir, 'index.html'));
});

app.listen(port, '0.0.0.0', () => {
  console.log('ACERO Y SAL escuchando en el puerto ' + port);
});
