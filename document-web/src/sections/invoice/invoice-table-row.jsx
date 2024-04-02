import PropTypes from 'prop-types';

import Button from '@mui/material/Button';
import MenuItem from '@mui/material/MenuItem';
import TableRow from '@mui/material/TableRow';
// import Checkbox from '@mui/material/Checkbox';
import TableCell from '@mui/material/TableCell';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import ListItemText from '@mui/material/ListItemText';

import { useBoolean } from 'src/hooks/use-boolean';

import { fDate } from 'src/utils/format-time';
import { fCurrency } from 'src/utils/format-number';

import Iconify from 'src/components/iconify';
import { ConfirmDialog } from 'src/components/custom-dialog';
import CustomPopover, { usePopover } from 'src/components/custom-popover';

// ----------------------------------------------------------------------

export default function InvoiceTableRow({
  row,
  selected,
  onSelectRow,
  onViewRow,
  onViewAlbaranRow,
  onEditRow,
  onDeleteRow,
}) {
  const { documentNumber, emitedAt, total } = row;

  const confirm = useBoolean();

  const popover = usePopover();

  return (
    <>
      <TableRow hover selected={selected}>
        {/* <TableCell padding="checkbox">
          <Checkbox checked={selected} onClick={onSelectRow} />
        </TableCell> */}

        <TableCell sx={{ display: 'flex', alignItems: 'center' }}>
          
          <ListItemText
            disableTypography
            primary={
              <Typography variant="body2" noWrap>
                {documentNumber}
              </Typography>
            }
          />
        </TableCell>

        <TableCell>
          <ListItemText
            primary={fDate(emitedAt, 'dd-MM-yyyy')}
            secondary=''
            primaryTypographyProps={{ typography: 'body2', noWrap: true }}
            secondaryTypographyProps={{
              mt: 0.5,
              component: 'span',
              typography: 'caption',
            }}
          />
        </TableCell>

        <TableCell>{fCurrency(total)}</TableCell>

        <TableCell align="right" sx={{ px: 1 }}>
          <IconButton color={popover.open ? 'inherit' : 'default'} onClick={popover.onOpen}>
            <Iconify icon="eva:more-vertical-fill" />
          </IconButton>
        </TableCell>
      </TableRow>

      <CustomPopover
        open={popover.open}
        onClose={popover.onClose}
        arrow="right-top"
        sx={{ width: 160 }}
      >
        <MenuItem
          onClick={() => {
            onViewRow();
            popover.onClose();
          }}
        >
          <Iconify icon="solar:eye-bold" />
          Factura
        </MenuItem>
        {
          (row.albaranNumber !== -1 && `${row.albaranNumber}`.trim() !== 'INVOICE' ) && (<MenuItem
            onClick={() => {
              onViewAlbaranRow();
              popover.onClose();
            }}
          >
            <Iconify icon="solar:eye-bold" />
            Albarán [{row.albaranNumber}]
          </MenuItem>)
        }

        {/* <MenuItem
          onClick={() => {
            onEditRow();
            popover.onClose();
          }}
        >
          <Iconify icon="eva:download-outline" />
          Download
        </MenuItem> */}
      </CustomPopover>

      <ConfirmDialog
        open={confirm.value}
        onClose={confirm.onFalse}
        title="Delete"
        content="Are you sure want to delete?"
        action={
          <Button variant="contained" color="error" onClick={onDeleteRow}>
            Delete
          </Button>
        }
      />
    </>
  );
}

InvoiceTableRow.propTypes = {
  onDeleteRow: PropTypes.func,
  onEditRow: PropTypes.func,
  onSelectRow: PropTypes.func,
  onViewRow: PropTypes.func,
  onViewAlbaranRow: PropTypes.func,
  row: PropTypes.object,
  selected: PropTypes.bool,
};
