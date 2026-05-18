import {
  Box,
  Card as MUICard,
  CardContent,
  CardMedia,
  CircularProgress,
  Typography,
  CardActions,
  Button,
} from '@mui/material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function Card({ hotel }) {
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const handleDetailsClick = (e) => {
    e.stopPropagation();
    navigate(`/hotel-details/${hotel.id}`);
  };

  return (
    <MUICard
      sx={{
        maxWidth: 345,
        transition: 'box-shadow 0.2s ease-in-out',
        '&:hover': {
          boxShadow: (theme) => theme.shadows[4],
        },
      }}
    >
      <Box sx={{ position: 'relative' }}>
        {loading && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: 'background.paper',
            }}
          >
            <CircularProgress />
          </Box>
        )}
        <CardMedia
          component="img"
          height="200"
          image={hotel.photo}
          alt={hotel.name}
          onLoad={() => setLoading(false)}
          onError={() => setLoading(false)}
          sx={{
            opacity: loading ? 0 : 1,
            transition: 'opacity 0.3s ease-in-out',
            objectFit: 'cover',
          }}
        />
      </Box>
      <CardContent>
        <Typography variant="h6" component="div" noWrap sx={{ mb: 1 }}>
          {hotel.name}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
          {hotel.city}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {hotel.phone_number}
        </Typography>
      </CardContent>
      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <Button size="small" variant="outlined" onClick={handleDetailsClick}>
          Details
        </Button>
        <Button
          size="small"
          variant="contained"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/booking/${hotel.id}`);
          }}
        >
          Book Now
        </Button>
      </CardActions>
    </MUICard>
  );
}
