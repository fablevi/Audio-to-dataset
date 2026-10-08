package com.fablevi.audiotodataset;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@ComponentScan(basePackages = {"com.fablevi.audiotodataset"})
public class AudiotodatasetApplication {

	public static void main(String[] args) {
		SpringApplication.run(AudiotodatasetApplication.class, args);
	}

}
