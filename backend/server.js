const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const csv = require('csv-parser');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Multer setup for file uploads
const upload = multer({ dest: 'uploads/' });

// Database setup
const dbPath = path.join(__dirname, '../data/jobs.db');
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Database connection error:', err);
  } else {
    console.log('Connected to SQLite database');
    initializeDatabase();
  }
});

// Initialize database tables
function initializeDatabase() {
  db.run(`
    CREATE TABLE IF NOT EXISTS jobs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      company TEXT NOT NULL,
      location TEXT NOT NULL,
      role TEXT NOT NULL,
      description TEXT,
      url TEXT,
      postedDate TEXT,
      salary TEXT,
      createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS applications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      jobId INTEGER NOT NULL,
      status TEXT DEFAULT 'interested',
      notes TEXT,
      appliedDate TEXT,
      createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (jobId) REFERENCES jobs(id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS bookmarks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      jobId INTEGER NOT NULL UNIQUE,
      createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (jobId) REFERENCES jobs(id)
    )
  `);
}

// API Routes

// Get all jobs with filters
app.get('/api/jobs', (req, res) => {
  const { role, location, search } = req.query;
  let query = 'SELECT * FROM jobs WHERE 1=1';
  const params = [];

  if (role) {
    query += ' AND role = ?';
    params.push(role);
  }

  if (location) {
    query += ' AND location = ?';
    params.push(location);
  }

  if (search) {
    query += ' AND (title LIKE ? OR company LIKE ?)';
    params.push(`%${search}%`, `%${search}%`);
  }

  db.all(query, params, (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json(rows);
  });
});

// Get single job with application status
app.get('/api/jobs/:id', (req, res) => {
  const { id } = req.params;
  db.get(
    `SELECT j.*, 
            (SELECT status FROM applications WHERE jobId = j.id LIMIT 1) as applicationStatus,
            (SELECT notes FROM applications WHERE jobId = j.id LIMIT 1) as applicationNotes,
            (SELECT COUNT(*) FROM bookmarks WHERE jobId = j.id) as isBookmarked
     FROM jobs j WHERE j.id = ?`,
    [id],
    (err, row) => {
      if (err) {
        res.status(500).json({ error: err.message });
        return;
      }
      if (!row) {
        res.status(404).json({ error: 'Job not found' });
        return;
      }
      res.json(row);
    }
  );
});

// Add a job
app.post('/api/jobs', (req, res) => {
  const { title, company, location, role, description, url, salary } = req.body;

  db.run(
    `INSERT INTO jobs (title, company, location, role, description, url, salary, postedDate)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
    [title, company, location, role, description, url, salary, new Date().toISOString()],
    function (err) {
      if (err) {
        res.status(500).json({ error: err.message });
        return;
      }
      res.status(201).json({ id: this.lastID, title, company, location, role });
    }
  );
});

// Update job
app.put('/api/jobs/:id', (req, res) => {
  const { id } = req.params;
  const { title, company, location, role, description, url, salary } = req.body;

  db.run(
    `UPDATE jobs SET title = ?, company = ?, location = ?, role = ?, description = ?, url = ?, salary = ?
     WHERE id = ?`,
    [title, company, location, role, description, url, salary, id],
    (err) => {
      if (err) {
        res.status(500).json({ error: err.message });
        return;
      }
      res.json({ success: true });
    }
  );
});

// Delete job
app.delete('/api/jobs/:id', (req, res) => {
  const { id } = req.params;

  db.run('DELETE FROM jobs WHERE id = ?', [id], (err) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json({ success: true });
  });
});

// Track application
app.post('/api/applications', (req, res) => {
  const { jobId, status, notes, appliedDate } = req.body;

  db.run(
    `INSERT OR REPLACE INTO applications (jobId, status, notes, appliedDate)
     VALUES (?, ?, ?, ?)`,
    [jobId, status || 'interested', notes || '', appliedDate || ''],
    function (err) {
      if (err) {
        res.status(500).json({ error: err.message });
        return;
      }
      res.status(201).json({ id: this.lastID, jobId, status });
    }
  );
});

// Get application for a job
app.get('/api/applications/:jobId', (req, res) => {
  const { jobId } = req.params;
  db.get(
    'SELECT * FROM applications WHERE jobId = ?',
    [jobId],
    (err, row) => {
      if (err) {
        res.status(500).json({ error: err.message });
        return;
      }
      res.json(row || {});
    }
  );
});

// Bookmark job
app.post('/api/bookmarks', (req, res) => {
  const { jobId } = req.body;

  db.run(
    'INSERT OR IGNORE INTO bookmarks (jobId) VALUES (?)',
    [jobId],
    function (err) {
      if (err) {
        res.status(500).json({ error: err.message });
        return;
      }
      res.status(201).json({ jobId });
    }
  );
});

// Remove bookmark
app.delete('/api/bookmarks/:jobId', (req, res) => {
  const { jobId } = req.params;

  db.run('DELETE FROM bookmarks WHERE jobId = ?', [jobId], (err) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    res.json({ success: true });
  });
});

// Get bookmarks
app.get('/api/bookmarks', (req, res) => {
  db.all(
    `SELECT j.* FROM jobs j 
     INNER JOIN bookmarks b ON j.id = b.jobId 
     ORDER BY b.createdAt DESC`,
    (err, rows) => {
      if (err) {
        res.status(500).json({ error: err.message });
        return;
      }
      res.json(rows);
    }
  );
});

// Import jobs from CSV
app.post('/api/import', upload.single('file'), (req, res) => {
  if (!req.file) {
    res.status(400).json({ error: 'No file uploaded' });
    return;
  }

  const results = [];
  fs.createReadStream(req.file.path)
    .pipe(csv())
    .on('data', (data) => results.push(data))
    .on('end', () => {
      const insertStmt = db.prepare(
        `INSERT INTO jobs (title, company, location, role, description, url, salary, postedDate)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      );

      results.forEach((row) => {
        insertStmt.run([
          row.title,
          row.company,
          row.location,
          row.role,
          row.description || '',
          row.url || '',
          row.salary || '',
          row.postedDate || new Date().toISOString(),
        ]);
      });

      insertStmt.finalize((err) => {
        fs.unlink(req.file.path, () => {}); // Clean up uploaded file
        if (err) {
          res.status(500).json({ error: err.message });
          return;
        }
        res.json({ success: true, imported: results.length });
      });
    })
    .on('error', (error) => {
      res.status(500).json({ error: error.message });
    });
});

// Get filter options
app.get('/api/filters', (req, res) => {
  const roles = ['UI/UX', 'Research', 'Analyst'];
  const locations = ['Ottawa', 'Guelph', 'Toronto', 'Mississauga'];

  res.json({ roles, locations });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
