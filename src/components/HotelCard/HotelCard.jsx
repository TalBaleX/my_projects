import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  Card,
  CardActions,
  CardContent,
  CardMedia,
  Button,
  Typography,
} from '@mui/material';

export const HotelCard = ({ hotel }) => {
  const navigate = useNavigate();
  const currentUser = useSelector((state) => state.users.currentUser);

  const handleBooking = () => {
    if (!currentUser) {
      navigate('/login', { state: { from: `/booking/${hotel.id}` } });
    } else {
      navigate(`/booking/${hotel.id}`);
    }
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardMedia
        component="img"
        height="140"
        image={hotel.photo}
        alt={hotel.name}
      />
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography gutterBottom variant="h5" component="div">
          {hotel.name}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {hotel.city}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {hotel.phone_number}
        </Typography>
      </CardContent>
      <CardActions>
        <Button
          size="small"
          onClick={() => navigate(`/hotel-details/${hotel.id}`)}
        >
          View Details
        </Button>
        <Button size="small" onClick={handleBooking}>
          Book Now
        </Button>
      </CardActions>
    </Card>
  );
};
