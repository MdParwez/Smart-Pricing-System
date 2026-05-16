import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControlLabel,
  Radio,
  RadioGroup,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
} from '@mui/material';
import { LocalizationProvider, DatePicker, TimePicker } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';

export default function ScheduleDialog({
  open,
  onClose,
  onScrapeNow,
  onSchedule,
  loading,
}) {
  const [runOption, setRunOption] = useState('now');
  const [scheduleDate, setScheduleDate] = useState(null);
  const [scheduleTime, setScheduleTime] = useState(null);
  const [timezone, setTimezone] = useState('IST');

  const handleSave = () => {
    if (runOption === 'now') {
      onScrapeNow();
    } else {
      onSchedule({
        scheduleDate,
        scheduleTime,
        timezone,
        runOption: 'schedule',
      });
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>How do you want to run the Report?</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          <RadioGroup value={runOption} onChange={(e) => setRunOption(e.target.value)}>
            <FormControlLabel
              value="now"
              control={<Radio />}
              label="Instant Report"
            />
            <FormControlLabel
              value="schedule"
              control={<Radio />}
              label="Schedule Report"
            />
          </RadioGroup>

          {runOption === 'schedule' && (
            <Box sx={{ mt: 3, display: 'grid', gap: 2 }}>
              <LocalizationProvider dateAdapter={AdapterDayjs}>
                <DatePicker
                  label="Select Date"
                  value={scheduleDate}
                  onChange={setScheduleDate}
                />
                <TimePicker
                  label="Select Time"
                  value={scheduleTime}
                  onChange={setScheduleTime}
                />
              </LocalizationProvider>

              <FormControl fullWidth>
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  label="Timezone"
                >
                  <MenuItem value="IST">India Standard Time (IST)</MenuItem>
                  <MenuItem value="UTC">UTC</MenuItem>
                  <MenuItem value="EST">Eastern Standard Time (EST)</MenuItem>
                  <MenuItem value="PST">Pacific Standard Time (PST)</MenuItem>
                </Select>
              </FormControl>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          color="success"
          disabled={
            loading ||
            (runOption === 'schedule' && (!scheduleDate || !scheduleTime))
          }
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {runOption === 'now' ? 'Start Now' : 'Schedule'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
