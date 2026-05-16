import React from 'react';
import {
  Box,
  FormControlLabel,
  Radio,
  RadioGroup,
  FormControl,
  Typography,
  Checkbox,
  FormGroup,
  Select,
  MenuItem,
  InputLabel,
} from '@mui/material';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';

const daysOfWeek = [
  { label: 'Monday', value: 'mon' },
  { label: 'Tuesday', value: 'tue' },
  { label: 'Wednesday', value: 'wed' },
  { label: 'Thursday', value: 'thu' },
  { label: 'Friday', value: 'fri' },
  { label: 'Saturday', value: 'sat' },
  { label: 'Sunday', value: 'sun' },
];

export default function DateSelection({ formData, onChange }) {
  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box sx={{ display: 'grid', gap: 3 }}>
        <Box>
          <Typography variant="subtitle1" sx={{ mb: 2 }}>
            Date Range Type
          </Typography>
          <RadioGroup
            value={formData.dateRange}
            onChange={(e) => onChange({ dateRange: e.target.value })}
            row
          >
            <FormControlLabel value="continuous" control={<Radio />} label="Continuous" />
            <FormControlLabel value="preferred" control={<Radio />} label="Preferred" />
          </RadioGroup>
        </Box>

        <Box>
          <Typography variant="subtitle2" sx={{ mb: 2 }}>
            Outbound Date Range
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <DatePicker
              label="From"
              value={formData.outboundDateFrom}
              onChange={(date) => onChange({ outboundDateFrom: date })}
            />
            <DatePicker
              label="To"
              value={formData.outboundDateTo}
              onChange={(date) => onChange({ outboundDateTo: date })}
            />
          </Box>
        </Box>

        {formData.journeyType === 'round-trip' && (
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 2 }}>
              Inbound Date Range
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <DatePicker
                label="From"
                value={formData.inboundDateFrom}
                onChange={(date) => onChange({ inboundDateFrom: date })}
              />
              <DatePicker
                label="To"
                value={formData.inboundDateTo}
                onChange={(date) => onChange({ inboundDateTo: date })}
              />
            </Box>
          </Box>
        )}

        <Box>
          <Typography variant="subtitle2" sx={{ mb: 2 }}>
            Days of Week
          </Typography>
          <FormGroup row>
            {daysOfWeek.map((day) => (
              <FormControlLabel
                key={day.value}
                control={
                  <Checkbox
                    checked={formData.daysOfWeek.includes(day.value)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        onChange({
                          daysOfWeek: [...formData.daysOfWeek, day.value],
                        });
                      } else {
                        onChange({
                          daysOfWeek: formData.daysOfWeek.filter(
                            (d) => d !== day.value
                          ),
                        });
                      }
                    }}
                  />
                }
                label={day.label}
              />
            ))}
          </FormGroup>
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr', gap: 2 }}>
          <FormControl fullWidth>
            <InputLabel>Departure Time</InputLabel>
            <Select
              value={formData.departureTime}
              onChange={(e) => onChange({ departureTime: e.target.value })}
              label="Departure Time"
            >
              <MenuItem value="any">Any Time</MenuItem>
              <MenuItem value="early-morning">Early Morning (00:00-06:00)</MenuItem>
              <MenuItem value="morning">Morning (06:00-12:00)</MenuItem>
              <MenuItem value="afternoon">Afternoon (12:00-18:00)</MenuItem>
              <MenuItem value="evening">Evening (18:00-24:00)</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <FormControlLabel
          control={
            <Checkbox
              checked={formData.considerFarthestDate}
              onChange={(e) =>
                onChange({ considerFarthestDate: e.target.checked })
              }
            />
          }
          label="Consider shopping from the farthest/last date"
        />
      </Box>
    </LocalizationProvider>
  );
}
