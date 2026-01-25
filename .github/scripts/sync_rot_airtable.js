// Airtable sync script with datestamped JSON output (no cron, single run)
require('dotenv').config();
const Airtable = require('airtable');
const fs = require('fs-extra');
const path = require('path');

// Config
const AIRTABLE_TOKEN = process.env.AIRTABLE_TOKEN;
const OUTPUT_DIR = path.join(__dirname, '..', '..', 'rot', 'airtable');

// Table configs: { name, baseId, tableId }
const TABLES = [
  { name: 'rolodex', baseId: 'appoLxmYQNacb9kYG', tableId: 'tbl6hjKmWrTkxDjCm' },
  { name: 'feedback', baseId: 'appnx6c8gKHwsIFgq', tableId: 'tblMtJiBiC19OXNoT' },
  { name: 'classifieds', baseId: 'app1NFJNAu8SCkWWJ', tableId: 'tbl8xoVhFQrJOeuSJ' },
  { name: 'content-tracker', baseId: 'appPbEum8wza4hcEc', tableId: 'tblHncmZVyKkK7PFq' },
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

// Run all table syncs once
async function main() {
  for (const cfg of TABLES) {
    await fetchAndSaveTable(cfg);
  }
}

main();
