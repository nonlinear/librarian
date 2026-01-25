// Airtable sync script with node-cron and datestamped JSON output
require('dotenv').config();
const Airtable = require('airtable');
const fs = require('fs-extra');
const path = require('path');
const cron = require('node-cron');

// Config
const AIRTABLE_TOKEN = process.env.AIRTABLE_TOKEN;

const OUTPUT_DIR = path.join(__dirname, '..', '..', 'rot', 'airtable');

// Table configs: { name, baseId, tableId }
const TABLES = [
  { name: 'rolodex', baseId: process.env.AIRTABLE_BASEID_ROLODEX, tableId: process.env.AIRTABLE_TABLEID_ROLODEX },
  { name: 'feedback', baseId: process.env.AIRTABLE_BASEID_FEEDBACK, tableId: process.env.AIRTABLE_TABLEID_FEEDBACK },
  { name: 'classifieds', baseId: process.env.AIRTABLE_BASEID_CLASSIFIEDS, tableId: process.env.AIRTABLE_TABLEID_CLASSIFIEDS },
  { name: 'content-tracker', baseId: process.env.AIRTABLE_BASEID_CONTENT_TRACKER, tableId: process.env.AIRTABLE_TABLEID_CONTENT_TRACKER },
];

if (!AIRTABLE_TOKEN) {
  console.error('Missing AIRTABLE_TOKEN in .env');
  process.exit(1);
}


async function fetchAndSaveTable({ name, baseId, tableId }) {
  const base = new Airtable({ apiKey: AIRTABLE_TOKEN }).base(baseId);
  const records = [];
  const now = new Date();
  const datestamp = now.toISOString().slice(0, 10); // YYYY-MM-DD
  const filename = `${name}-${datestamp}.json`;
  const filepath = path.join(OUTPUT_DIR, filename);

  try {
    await fs.ensureDir(OUTPUT_DIR);
    await base(tableId)
      .select({})
      .eachPage((pageRecords, fetchNextPage) => {
        records.push(...pageRecords.map(r => r.fields));
        fetchNextPage();
      });
    const output = {
      datestamp,
      count: records.length,
      records
    };

    // Check if data changed (compare to most recent file)
    const files = (await fs.readdir(OUTPUT_DIR))
      .filter(f => f.startsWith(name + '-') && f.endsWith('.json'))
      .sort().reverse();
    let changed = true;
    if (files.length > 0) {
      const lastFile = await fs.readJson(path.join(OUTPUT_DIR, files[0]));
      changed = JSON.stringify(lastFile.records) !== JSON.stringify(records);
    }
    if (changed) {
      await fs.writeJson(filepath, output, { spaces: 2 });
      console.log(`Saved ${records.length} records to ${filepath}`);
    } else {
      console.log(`[${name}] No changes, not saving new snapshot.`);
    }

    // Keep only 5 most recent files
    const updatedFiles = (await fs.readdir(OUTPUT_DIR))
      .filter(f => f.startsWith(name + '-') && f.endsWith('.json'))
      .sort().reverse();
    for (let i = 5; i < updatedFiles.length; i++) {
      await fs.remove(path.join(OUTPUT_DIR, updatedFiles[i]));
      console.log(`[${name}] Deleted old snapshot: ${updatedFiles[i]}`);
    }
  } catch (err) {
    console.error(`Error fetching/saving Airtable for ${name}:`, err);
  }
}


// Run every hour at minute 0
cron.schedule('0 * * * *', () => {
  TABLES.forEach(cfg => fetchAndSaveTable(cfg));
});

// Run once on startup
TABLES.forEach(cfg => fetchAndSaveTable(cfg));
