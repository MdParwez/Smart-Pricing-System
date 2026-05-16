import React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  FormControlLabel,
  Checkbox,
  Typography,
  Paper,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';

export default function JourneyInformation({ formData, onChange }) {
  const [routes, setRoutes] = React.useState([{ origin: '', destination: '' }]);

  const addRoute = () => {
    setRoutes([...routes, { origin: '', destination: '' }]);
  };

  const updateRoute = (index, field, value) => {
    const newRoutes = [...routes];
    newRoutes[index][field] = value;
    setRoutes(newRoutes);
    onChange({ origin: newRoutes[0]?.origin || '', destination: newRoutes[0]?.destination || '' });
  };

  return (
    <Box sx={{ display: 'grid', gap: 3 }}>
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
        <FormControl fullWidth>
          <InputLabel>Journey Type</InputLabel>
          <Select
            value={formData.journeyType}
            onChange={(e) => onChange({ journeyType: e.target.value })}
            label="Journey Type"
          >
            <MenuItem value="one-way">One Way</MenuItem>
            <MenuItem value="round-trip">Round Trip</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Class of Service</InputLabel>
          <Select
            value={formData.classOfService}
            onChange={(e) => onChange({ classOfService: e.target.value })}
            label="Class of Service"
          >
            <MenuItem value="economy">Economy</MenuItem>
            <MenuItem value="premium-economy">Premium Economy</MenuItem>
            <MenuItem value="business">Business</MenuItem>
            <MenuItem value="first">First</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Stops</InputLabel>
          <Select
            value={formData.stops}
            onChange={(e) => onChange({ stops: e.target.value })}
            label="Stops"
          >
            <MenuItem value="non-stop">Non Stop</MenuItem>
            <MenuItem value="one-stop">1 Stop</MenuItem>
            <MenuItem value="two-plus-stops">2+ Stops</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel>Airline</InputLabel>
          <Select
            value={formData.airline}
            onChange={(e) => onChange({ airline: e.target.value })}
            label="Airline"
          >
            <MenuItem value="all">All Airlines</MenuItem>
            <MenuItem value="6E">IndiGo (6E)</MenuItem>
            <MenuItem value="AI">Air India (AI)</MenuItem>
            <MenuItem value="SG">SpiceJet (SG)</MenuItem>
            <MenuItem value="IX">Air India Express (IX)</MenuItem>
            <MenuItem value="QP">Akasa Air (QP)</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Box>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Routes
        </Typography>
        <Paper sx={{ p: 2, backgroundColor: '#f9f9f9' }}>
          {routes.map((route, index) => (
            <Box key={index} sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 2, mb: 2 }}>
              <TextField
                label="Origin (e.g., DEL)"
                value={route.origin}
                onChange={(e) => updateRoute(index, 'origin', e.target.value)}
                placeholder="DEL"
              />
              <TextField
                label="Destination (e.g., BOM)"
                value={route.destination}
                onChange={(e) => updateRoute(index, 'destination', e.target.value)}
                placeholder="BOM"
              />
            </Box>
          ))}
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={addRoute}
            sx={{ mt: 1 }}
          >
            Add Route
          </Button>
        </Paper>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Passengers
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 1 }}>
            <TextField
              label="Adults"
              type="number"
              value={formData.passengerType.adult}
              onChange={(e) =>
                onChange({
                  passengerType: {
                    ...formData.passengerType,
                    adult: parseInt(e.target.value) || 0,
                  },
                })
              }
              inputProps={{ min: 0 }}
            />
            <TextField
              label="Children"
              type="number"
              value={formData.passengerType.child}
              onChange={(e) =>
                onChange({
                  passengerType: {
                    ...formData.passengerType,
                    child: parseInt(e.target.value) || 0,
                  },
                })
              }
              inputProps={{ min: 0 }}
            />
            <TextField
              label="Infants"
              type="number"
              value={formData.passengerType.infant}
              onChange={(e) =>
                onChange({
                  passengerType: {
                    ...formData.passengerType,
                    infant: parseInt(e.target.value) || 0,
                  },
                })
              }
              inputProps={{ min: 0 }}
            />
          </Box>
        </Box>

        <Box>
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.reverseOND}
                onChange={(e) => onChange({ reverseOND: e.target.checked })}
              />
            }
            label="Reverse OND"
          />
        </Box>
      </Box>
    </Box>
  );
}
