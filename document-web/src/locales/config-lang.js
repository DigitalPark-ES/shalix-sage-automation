import merge from 'lodash/merge';
// date fns
import {
  es as esESAdapter,
  enUS as enUSAdapter,
} from 'date-fns/locale';

// core (MUI)
import {
  enUS as enUSCore,
  esES as esESCore,
} from '@mui/material/locale';
// data grid (MUI)
import {
  enUS as enUSDataGrid,
  esES as esESDataGrid,
} from '@mui/x-data-grid';
// date pickers (MUI)
import {
  enUS as enUSDate,
  esES as esESDate,
} from '@mui/x-date-pickers/locales';

// PLEASE REMOVE `LOCAL STORAGE` WHEN YOU CHANGE SETTINGS.
// ----------------------------------------------------------------------

export const allLangs = [
  {
    label: 'English',
    value: 'en',
    systemValue: merge(enUSDate, enUSDataGrid, enUSCore),
    adapterLocale: enUSAdapter,
    icon: 'flagpack:gb-nir',
    numberFormat: {
      code: 'en-US',
      currency: 'USD',
    },
  },
  {
    label: 'Español',
    value: 'es',
    systemValue: merge(esESDate, esESDataGrid, esESCore),
    adapterLocale: esESAdapter,
    icon: 'flagpack:es',
    numberFormat: {
      code: 'en-ES',
      currency: 'EUR',
    },
  },
];

export const defaultLang = allLangs[1]; // Spanish

// GET MORE COUNTRY FLAGS
// https://icon-sets.iconify.design/flagpack/
// https://www.dropbox.com/sh/nec1vwswr9lqbh9/AAB9ufC8iccxvtWi3rzZvndLa?dl=0
