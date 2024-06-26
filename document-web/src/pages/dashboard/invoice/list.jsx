import { Helmet } from 'react-helmet-async';
import { useAuthContext } from 'src/auth/hooks';

import { InvoiceListView } from 'src/sections/invoice/view';

// ----------------------------------------------------------------------

export default function InvoiceListPage() {
  const { user } = useAuthContext();
  return (
    <>
      <Helmet>
        <title>Dashboard: Facturas</title>
      </Helmet>

      <InvoiceListView documentType='INVOICE' cif={user.cif} heading='Facturas'/>
    </>
  );
}
