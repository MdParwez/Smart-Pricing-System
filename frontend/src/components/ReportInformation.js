import React from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';

export default function ReportInformation({ formData, onChange }) {
  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
      <TextField
        label="Report Name"
        value={formData.reportName}
        onChange={(e) => onChange({ reportName: e.target.value })}
        fullWidth
        variant="outlined"
        required
      />
      <FormControl fullWidth>
        <InputLabel>Report Type</InputLabel>
        <Select
          value={formData.reportType}
          onChange={(e) => onChange({ reportType: e.target.value })}
          label="Report Type"
        >
          <MenuItem value="standard">Standard</MenuItem>
          <MenuItem value="competitive">Competitive Analysis</MenuItem>
          <MenuItem value="pricing">Pricing Strategy</MenuItem>
        </Select>
      </FormControl>
      <TextField
        label="Report Description"
        value={formData.reportDescription}
        onChange={(e) => onChange({ reportDescription: e.target.value })}
        fullWidth
        variant="outlined"
        multiline
        rows={4}
        sx={{ gridColumn: '1 / -1' }}
      />
      <TextField
        label="User Notes"
        value={formData.userNotes}
        onChange={(e) => onChange({ userNotes: e.target.value })}
        fullWidth
        variant="outlined"
        multiline
        rows={4}
        sx={{ gridColumn: '1 / -1' }}
      />
    </Box>
  );
}
