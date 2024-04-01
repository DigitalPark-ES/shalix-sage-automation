import { useState } from "react";
import { query, where, getDocs, collection, getFirestore } from "firebase/firestore";

import { firebaseApp } from "src/auth/context/firebase/lib";

const DB = getFirestore(firebaseApp);

export function useGetDocuments(documentType, cif) {
    const [documents, setDocuments] = useState([]);
    const [fetching, setFetching] = useState(false);

    const fetch = async () => {
        setFetching(true);
        const docs = await getDocs(
            query(collection(DB, 'documents'), 
                where("doc_type", "==", documentType),
                where("cif", "==", cif),
            ));
        if(!docs.empty) {
            setDocuments(docs.docs.map(c => {
                const data = c.data();
                const dateParts = data.emited_at.split('-');
                return {
                    id: c.id,
                    documentNumber: data.doc_number,
                    total: parseFloat(data.total),
                    emitedAt: new Date(
                        parseInt(dateParts[2], 10), 
                        parseInt(dateParts[1], 10) - 1, 
                        parseInt(dateParts[0], 10))
                };
            }));
        } else {
            setDocuments([]);
        }
        setFetching(false);
    }

    return {
        fetching,
        documents,
        fetch
    };
}