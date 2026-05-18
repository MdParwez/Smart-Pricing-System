import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  FormControlLabel,
  Grid,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff';
import { scraperService } from '../services/scraperService';

const AirlineSelection = ({ onAirlineSelect, onCompetitorsChange }) => {
  const [airlines, setAirlines] = useState([]);
  const [selectedAirline, setSelectedAirline] = useState(null);
  const [includeCompetitors, setIncludeCompetitors] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAirlines = async () => {
      try {
        setLoading(true);
        const data = await scraperService.listAirlines();
        setAirlines(data.airlines || []);
      } catch (err) {
        setError(`Failed to load airlines: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchAirlines();
  }, []);

  const handleAirlineSelect = async (airlineName) => {
    try {
      setError('');
      const config = await scraperService.getAirlineConfig(airlineName);
      setSelectedAirline(config);
      onAirlineSelect(config);
    } catch (err) {
      setError(`Failed to load airline config: ${err.message}`);
    }
  };

  const handleCompetitorsToggle = (event) => {
    const enabled = event.target.checked;
    setIncludeCompetitors(enabled);
    onCompetitorsChange(enabled);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper elevation={2} sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h5" fontWeight={600}>
            Select Airline
          </Typography>
          <Typography color="text.secondary">
            Choose the primary airline for the fare scrape.
          </Typography>
        </Box>

        {error && <Alert severity="error">{error}</Alert>}

        <Grid container spacing={2}>
          {airlines.map((airline) => (
            <Grid item xs={12} sm={6} md={4} key={airline}>
              <Button
                fullWidth
                variant={selectedAirline?.airline === airline ? 'contained' : 'outlined'}
                onClick={() => handleAirlineSelect(airline)}
                startIcon={<FlightTakeoffIcon />}
                sx={{ justifyContent: 'flex-start', minHeight: 64 }}
              >
                <Box sx={{ textAlign: 'left' }}>
                  <Typography fontWeight={600}>{airline}</Typography>
                  <Typography variant="caption">Select to scrape</Typography>
                </Box>
              </Button>
            </Grid>
          ))}
        </Grid>

        {selectedAirline && (
          <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Available Routes
            </Typography>
            <Grid container spacing={1.5} sx={{ mb: 2 }}>
              {selectedAirline.routes?.map((route) => (
                <Grid item xs={12} md={6} key={`${route.origin}-${route.destination}`}>
                  <Paper variant="outlined" sx={{ p: 1.5, bgcolor: 'primary.50' }}>
                    <Typography variant="body2" fontWeight={600}>
                      {route.origin_name} ({route.origin}) to {route.destination_name} ({route.destination})
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>

            {selectedAirline.competitors?.length > 0 && (
              <Stack spacing={1}>
                <FormControlLabel
                  control={
                    <Checkbox checked={includeCompetitors} onChange={handleCompetitorsToggle} />
                  }
                  label="Include configured competitors"
                />
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  {selectedAirline.competitors.map((competitor) => (
                    <Chip key={competitor} label={competitor} size="small" />
                  ))}
                </Stack>
              </Stack>
            )}
          </Box>
        )}
      </Stack>
    </Paper>
  );
};

export default AirlineSelection;
