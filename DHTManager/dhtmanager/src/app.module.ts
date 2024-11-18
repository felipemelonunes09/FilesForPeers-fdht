import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ResourcesModule } from './resources/resources.module';
import { ConfigModule } from '@nestjs/config'
import { configuration } from './configuration'

@Module({
  imports: [
    ResourcesModule, 
    ConfigModule.forRoot({isGlobal: true, load: [configuration]})
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
