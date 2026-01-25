---
category: automation
tags: [ios, shortcuts, icloud, safari, workflow]
description: Create and integrate iOS Shortcuts with Mac workflow, including iCloud Drive integration
---

# New iOS Shortcut - Integration Guide

## iCloud Drive Access for Shortcuts

**Shortcuts folder path on Mac:**

```
/Users/nfrota/Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents/
```

This folder syncs with **iCloud Drive → Shortcuts** on iOS/iPadOS devices.

## Creating File-Based Shortcuts

### Basic Flow:

1. **iOS Shortcut** generates data (text, markdown, JSON, etc.)
2. Saves to **iCloud Drive → Shortcuts folder**
3. **Mac** reads file automatically or via script
4. Process data and integrate into workflow

### Common Actions in Shortcuts:

**Get Safari Tabs:**

- Action: `Get Safari Web Pages`
- Returns: Array of current tabs

**Format as Markdown:**

```
- [Name](URL)
```

Use "Text" action with magic variables

**Save to iCloud:**

- Action: `Save File`
- Location: `iCloud Drive → Shortcuts`
- Filename: Include timestamp for uniqueness

**Clear Safari Tabs (optional):**

- Action: `Close All Tabs with Safari`

### Example Shortcut Structure:

```
1. Get Safari Web Pages
2. Repeat with Each (web page)
   - Get Name of Safari Web Page
   - Get URL of Safari Web Page
   - Text: "- [Name](URL)"
   - Add to Variable: MarkdownList
3. End Repeat
4. Get Device Details (Device Name)
5. Get Current Date → Format Date
6. Combine Text:
   # [Device Name] - [Timestamp]

   [MarkdownList]
7. Save File to iCloud Drive → Shortcuts
8. Show Notification: "✅ Exported!"
```

## Reading Shortcut Output on Mac

### Method 1: Direct File Read

```bash
cat "/Users/nfrota/Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents/safari-tabs-export.md"
```

### Method 2: Monitor Folder (watch script)

```bash
#!/bin/bash
SHORTCUTS_DIR="/Users/nfrota/Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents"
fswatch -0 "$SHORTCUTS_DIR" | while read -d "" event; do
    echo "New file detected: $event"
    # Process file here
done
```

### Method 3: Copilot Tool

Ask Copilot to read the file and process automatically:

- Read file contents
- Parse markdown links
- Extract URLs and titles
- Organize into target document

## Common Shortcut Patterns

### Export to Notes (alternative)

- Action: `Create Note`
- Note: `[Generated content]`
- Show Compose Sheet: OFF
- Notes sync via iCloud

### Export to Clipboard (simplest)

- Action: `Copy to Clipboard`
- Universal Clipboard syncs to Mac
- Paste directly into files

### Clean Up After Export

- Delete tabs: `Close All Tabs with Safari`
- Archive old files: Move to dated folder
- Send notification with summary

## File Naming Conventions

**Timestamp-based:**

```
safari-tabs-2025-01-16-14-30.md
```

**Device-based:**

```
iPhone-tabs-export.md
iPad-tabs-export.md
```

**Purpose-based:**

```
character-design-courses.md
research-links.md
```

## Debugging Shortcuts

### Check iCloud Sync:

```bash
ls -lat "/Users/nfrota/Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents/" | head -20
```

### Verify file contents:

```bash
tail -f "/Users/nfrota/Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents/safari-tabs-export.md"
```

### Common Issues:

- **File not appearing:** Wait 5-10s for iCloud sync
- **Permission denied:** Check Shortcuts app has iCloud access
- **Empty file:** Shortcut may have failed silently - add notifications
- **Old data:** Use timestamps in filenames to avoid overwriting

## Integration Examples

### Export Safari Tabs → Organize Courses

1. Run shortcut on iPhone
2. File appears in Shortcuts folder
3. Copilot reads file
4. Extracts URLs and titles
5. Populates course comparison template
6. Archives export file

### Capture Research → Knowledge Base

1. Shortcut exports Reading List
2. Saves to iCloud with tags
3. Script processes and categorizes
4. Adds to Hugo content/ideas/
5. Builds site with new research

### Quick Notes → TODO System

1. Shortcut creates timestamped note
2. Saves to Shortcuts folder
3. Parser extracts tasks
4. Updates TODO.md or project files
5. Deletes processed note

## Tips & Best Practices

- **Always include timestamps** in output for tracking
- **Add device name** to distinguish iPhone vs iPad exports
- **Use notifications** to confirm successful runs
- **Keep filenames simple** - avoid spaces and special chars
- **Test with small datasets** first before bulk operations
- **Archive old exports** periodically to avoid clutter
- **Use magic variables** in Shortcuts instead of manual text
- **Enable "Show in Share Sheet"** for easy access from Safari

## Next Steps

When creating a new shortcut:

1. Define the data source (Safari, Photos, Contacts, etc.)
2. Format the output (Markdown, JSON, CSV, plain text)
3. Choose save location (iCloud Shortcuts folder recommended)
4. Test sync between devices
5. Create Mac-side script if needed for processing
6. Document the workflow in relevant project files
