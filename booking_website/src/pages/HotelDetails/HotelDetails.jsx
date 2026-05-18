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

export function HotelDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const hotel = useSelector((state) =>
    state.hotels.hotels.find((h) => h.id === id || h.id === parseInt(id))
  );

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
        <Container maxWidth="md" sx={{ my: 4 }}>
          <Card>
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
                Contact: {hotel.phone_number}
              </Typography>
            </CardContent>
            <CardActions>
              <Button
                size="large"
                variant="contained"
                onClick={() => navigate(`/booking/${hotel.id}`)}
              >
                Book Now
              </Button>
              <Button size="large" onClick={() => navigate('/hotels')}>
                Back to Hotels
              </Button>
            </CardActions>
          </Card>
        </Container>
      )}
      renderFooter={() => <Footer />}
    />
  );
}
