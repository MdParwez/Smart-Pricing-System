import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Grid,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import RouteIcon from '@mui/icons-material/Route';

const RouteSelection = ({ airline, onRouteSelect }) => {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [availableRoutes, setAvailableRoutes] = useState([]);
  const [airportCodes, setAirportCodes] = useState({});

  useEffect(() => {
    if (!airline) return;

    setAirportCodes(airline.airport_codes || {});
    setAvailableRoutes(airline.routes || []);

    if (airline.routes?.length > 0) {
      const firstRoute = airline.routes[0];
      setOrigin(firstRoute.origin);
      setDestination(firstRoute.destination);
      onRouteSelect({
        origin: firstRoute.origin,
        destination: firstRoute.destination,
      });
    }
  }, [airline, onRouteSelect]);

  const handleRouteSelect = (route) => {
    setOrigin(route.origin);
    setDestination(route.destination);
    onRouteSelect({
      origin: route.origin,
      destination: route.destination,
    });
  };

  const handleCustomRoute = () => {
    if (!origin.trim() || !destination.trim()) return;

    onRouteSelect({
      origin: origin.trim().toUpperCase(),
      destination: destination.trim().toUpperCase(),
    });
  };

  return (
    <Paper elevation={2} sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h5" fontWeight={600}>
            Select Route
          </Typography>
          <Typography color="text.secondary">
            Choose a configured route or enter custom IATA airport codes.
          </Typography>
        </Box>

        {availableRoutes.length > 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Configured Routes
            </Typography>
            <Grid container spacing={2}>
              {availableRoutes.map((route) => (
                <Grid item xs={12} md={6} key={`${route.origin}-${route.destination}`}>
                  <Button
                    fullWidth
                    variant={
                      origin === route.origin && destination === route.destination
                        ? 'contained'
                        : 'outlined'
                    }
                    onClick={() => handleRouteSelect(route)}
                    startIcon={<RouteIcon />}
                    sx={{ justifyContent: 'flex-start', minHeight: 72 }}
                  >
                    <Box sx={{ textAlign: 'left' }}>
                      <Typography fontWeight={600}>
                        {route.origin_name} ({route.origin})
                      </Typography>
                      <Typography variant="caption">
                        to {route.destination_name} ({route.destination})
                      </Typography>
                    </Box>
                  </Button>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Custom Route
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={5}>
              <TextField
                fullWidth
                label="Origin"
                placeholder="DUB"
                value={origin}
                onChange={(event) => setOrigin(event.target.value.toUpperCase().slice(0, 3))}
                inputProps={{ maxLength: 3 }}
              />
            </Grid>
            <Grid item xs={12} sm={5}>
              <TextField
                fullWidth
                label="Destination"
                placeholder="LHR"
                value={destination}
                onChange={(event) => setDestination(event.target.value.toUpperCase().slice(0, 3))}
                inputProps={{ maxLength: 3 }}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <Button fullWidth variant="contained" onClick={handleCustomRoute}>
                Use
              </Button>
            </Grid>
          </Grid>
        </Box>

        {Object.keys(airportCodes).length > 0 && (
          <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Typography fontWeight={600} gutterBottom>
              Airport Codes
            </Typography>
            <Grid container spacing={1}>
              {Object.entries(airportCodes).map(([code, name]) => (
                <Grid item xs={6} md={3} key={code}>
                  <Typography variant="body2">
                    <strong>{code}</strong> - {name}
                  </Typography>
                </Grid>
              ))}
            </Grid>
          </Paper>
        )}
      </Stack>
    </Paper>
  );
};

export default RouteSelection;
