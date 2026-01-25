// Download images for exercises using node-fetch and update markdown paths
const fs = require('fs');
const path = require('path');
const fetch = (...args) => import('node-fetch').then(mod => mod.default(...args));

const images = [
  {
    url: 'https://upload.wikimedia.org/wikipedia/commons/2/2e/Chest_press_machine.jpg',
    name: 'seated-cable-chest-press.jpg'
  },
  {
    url: 'https://upload.wikimedia.org/wikipedia/commons/6/6e/Incline_bench_press.jpg',
    name: 'incline-cable-chest-press.jpg'
  },
  {
    url: 'https://upload.wikimedia.org/wikipedia/commons/2/2b/Cable_crossover.jpg',
    name: 'cable-fly.jpg'
  },
  {
    url: 'https://upload.wikimedia.org/wikipedia/commons/2/2a/Triceps_pushdown.jpg',
    name: 'triceps-pushdown.jpg'
  },
  {
    url: 'https://upload.wikimedia.org/wikipedia/commons/2/2c/Lying_triceps_extension.jpg',
    name: 'lying-triceps-extension.jpg'
  },
  {
    url: 'https://upload.wikimedia.org/wikipedia/commons/2/2a/Triceps_pushdown.jpg',
    name: 'reverse-grip-triceps-pushdown.jpg'
  },
  {
    url: 'https://upload.wikimedia.org/wikipedia/commons/2/2e/Shoulder_press.jpg',
    name: 'dumbbell-shoulder-press.jpg'
  },
  {
    url: 'https://upload.wikimedia.org/wikipedia/commons/2/2d/Cable_crunch.jpg',
    name: 'cable-crunch.jpg'
  }
];

const outDir = path.join(__dirname, '../../code/health/images');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

async function downloadImage(url, dest) {
  const res = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; ExerciseImageBot/1.0)'
    }
  });
  if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.status}`);
  const fileStream = fs.createWriteStream(dest);
  await new Promise((resolve, reject) => {
    res.body.pipe(fileStream);
    res.body.on('error', reject);
    fileStream.on('finish', resolve);
  });
}

(async () => {
  for (const img of images) {
    const dest = path.join(outDir, img.name);
    if (!fs.existsSync(dest)) {
      console.log(`Downloading ${img.url} -> ${dest}`);
      try {
        await downloadImage(img.url, dest);
      } catch (err) {
        console.error(err.message);
      }
    } else {
      console.log(`Already exists: ${dest}`);
    }
  }
  console.log('All images downloaded.');
})();
