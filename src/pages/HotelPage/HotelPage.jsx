import { useParams, useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  Card,
  CardActions,
  CardContent,
  CardMedia,
  Button,
  Typography,
  Container,
  Alert,
} from '@mui/material';
import { PageLayout, Header, Footer } from '@components';

export const HotelPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const hotels = useSelector((state) => state.hotels.hotels);
  const hotel = hotels.find((hotel) => hotel.id === id);

  if (!hotel) {
    return (
      <PageLayout
        renderHeader={() => <Header />}
        renderContent={() => (
          <Container>
            <Alert severity="error" sx={{ mt: 4 }}>
              Hotel not found
              <Button
                color="inherit"
                size="small"
                sx={{ ml: 2 }}
                onClick={() => navigate('/hotels')}
              >
                Return to Hotels
              </Button>
            </Alert>
          </Container>
        )}
        renderFooter={() => <Footer />}
      />
    );
  }

  return (
    <PageLayout
      renderHeader={() => <Header />}
      renderContent={() => (
        <Container maxWidth="md">
          <Card sx={{ marginTop: 5 }}>
            <CardMedia
              component="img"
              height="400"
              image={hotel.photo}
              alt={hotel.name}
            />
            <CardContent>
              <Typography gutterBottom variant="h4" component="div">
                {hotel.name}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {hotel.city}, {hotel.country}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {hotel.description}
              </Typography>
            </CardContent>
            <CardActions>
              <Button
                size="small"
                onClick={() => navigate(`/booking/${hotel.id}`)}
              >
                Book Now
              </Button>
              <Button size="small" onClick={() => navigate('/hotels')}>
                Back to Hotels
              </Button>
            </CardActions>
          </Card>
        </Container>
      )}
      renderFooter={() => <Footer />}
    />
  );
};
