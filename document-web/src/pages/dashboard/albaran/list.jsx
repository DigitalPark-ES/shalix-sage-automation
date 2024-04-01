import { Helmet } from 'react-helmet-async';
import { useAuthContext } from 'src/auth/hooks';

import { InvoiceListView } from 'src/sections/invoice/view';

// ----------------------------------------------------------------------

export default function AlbaranListPage() {
  const { user } = useAuthContext();
  return (
    <>
      <Helmet>
        <title>Dashboard: Albaranes</title>
      </Helmet>

      <InvoiceListView documentType='ALBARAN' cif={user.cif} heading='Albaranes'/>
    </>
  );
}
