// import {onRequest} from "firebase-functions/v2/https";
import { onDocumentCreated} from "firebase-functions/v2/firestore";
import * as logger from "firebase-functions/logger";
import {getAuth} from 'firebase-admin/auth';
// import {getFirestore} from 'firebase-admin/firestore';
import { initializeApp } from "firebase-admin/app";
import { getFirestore } from "firebase-admin/firestore";


initializeApp()

// export const helloWorld = onRequest((request, response) => {
//   logger.info("Hello logs!", {structuredData: true});
//   response.send("Hello from Firebase!");
// });

export const onUserCreated = onDocumentCreated("/users/{userId}", async (event) => {
  logger.info("Creating new user with data: ", event.data);
  const newUserId: string = event.params.userId;
  const email: string = event.data?.get("email");
  const cif: string = event.data?.get("cif");
  const password: string = cif;
  const name: string = event.data?.get("name");
  const lastName: string = event.data?.get("lastName");
  // const address: string = event.data?.get("address");
    
  const userRecord = await getAuth().createUser( {
    email,
    password,
    displayName: `${name} ${lastName}`
  });

  const userId = {userId: userRecord.uid};

  await getFirestore().collection('users').doc(newUserId).update({
    uid: userId.userId
  });

  // await getFirestore().collection('users').add({
  //   email,
  //   name,
  //   lastName,
  //   displayName: `${name} ${lastName}`,
  //   cif
  // })

  logger.info("New user created: " + email + ", with id: " + userId);

});
