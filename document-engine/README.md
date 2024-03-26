# Invoice Organizer Shalix

## Setup
Install python, pip and virtualenv

## Create Environment
```
$ virtualenv shalix
$ source shalix/bin/activate
```

## Prepare the Test information
1. Create the `workspace/input` folder and copy a pdf with Invoices. You can copy the example pdf file with 19 invoices from the `resources/test` folder.
```
$ mkdir -p workspace/input
$ cp resources/test/all_invoices.pdf workspace/input
```

2. Execute:
```
$ python src/invoice_splitter.py
```
