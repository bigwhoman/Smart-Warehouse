package main

import (
	"IoTProject_server/API"
	"IoTProject_server/util"
	"fmt"
	"github.com/gorilla/mux"
	"net/http"
)

var running_port = "8080"

func main() {

	util.GenerateQRhexCode()
	fmt.Println("Starting server...")
	util.Initializedatabase()
	handleRequests()
}
func handleRequests() {
	router := mux.NewRouter().StrictSlash(true)
	router.HandleFunc("/signup", API.Signup)
	router.HandleFunc("/login", API.Login)
	router.HandleFunc("/rentbox", API.RentBoxRequest)
	router.HandleFunc("/sendqr", API.SendingQR)
	router.HandleFunc("/isrented", API.IsRented)
	http.ListenAndServe(":"+running_port, router)
}
