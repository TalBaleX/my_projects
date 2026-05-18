import { createPortal } from 'react-dom';

export const createDialogPortal = (children) => {
  const portalNode = document.createElement('div');
  portalNode.setAttribute('data-dialog-portal', '');
  document.body.appendChild(portalNode);

  const portal = createPortal(children, portalNode);

  const cleanup = () => {
    if (portalNode && document.body.contains(portalNode)) {
      document.body.removeChild(portalNode);
    }
  };

  return { portal, cleanup };
};
