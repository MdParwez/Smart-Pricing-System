import React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Paper,
  Alert,
} from '@mui/material';

export default function ChannelSelection({ formData, onChange }) {
  return (
    <Box sx={{ display: 'grid', gap: 3 }}>
      <Typography variant="h6">Select Scraping Source</Typography>
      
      <FormControl fullWidth>
        <InputLabel>Channel</InputLabel>
        <Select
          value={formData.channel}
          onChange={(e) => onChange({ channel: e.target.value })}
          label="Channel"
        >
          <MenuItem value="playwright">Playwright Scraper (Current)</MenuItem>
          <MenuItem value="api" disabled>
            API Source (Future)
          </MenuItem>
          <MenuItem value="manual-upload" disabled>
            Manual Upload (Future)
          </MenuItem>
        </Select>
      </FormControl>

      <Paper sx={{ p: 2, backgroundColor: '#e3f2fd', borderLeft: '4px solid #1976d2' }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
          Current Selection: {formData.channel === 'playwright' ? 'Playwright Web Scraper' : 'Unknown'}
        </Typography>
        {formData.channel === 'playwright' && (
          <Typography variant="body2">
            Uses Playwright to automatically scrape flight prices from MakeMyTrip in real-time. 
            Fast, reliable, and handles JavaScript-rendered content.
          </Typography>
        )}
      </Paper>

      <Alert severity="info">
        The selected channel will determine where the fare data is collected from.
        Current: Live web scraping via Playwright.
      </Alert>
    </Box>
  );
}
