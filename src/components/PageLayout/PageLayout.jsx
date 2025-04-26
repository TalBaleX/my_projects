import { Box, Container } from '@mui/material';
import { forwardRef, memo } from 'react';

const PageLayoutComponent = forwardRef(function PageLayout(
  { renderHeader, renderFooter, renderContent, children },
  ref
) {
  const header = renderHeader?.();
  const content = renderContent ? renderContent() : children;
  const footer = renderFooter?.();

  return (
    <Box
      ref={ref}
      component="div"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        margin: 0,
        padding: 0,
        width: '100%',
        overflow: 'hidden',
      }}
    >
      <Box component="header">{header}</Box>
      <Container
        component="main"
        maxWidth="xl"
        sx={{
          flex: '1 0 auto',
          py: 3,
          px: { xs: 2, sm: 3 },
        }}
      >
        {content}
      </Container>
      <Box component="footer" sx={{ flex: '0 0 auto', p: 5 }}>
        <Container>{footer}</Container>
      </Box>
    </Box>
  );
});

PageLayoutComponent.displayName = 'PageLayout';

export const PageLayout = memo(PageLayoutComponent);
