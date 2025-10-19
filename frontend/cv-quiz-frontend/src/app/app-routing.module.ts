import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { QuizComponent } from './quiz/quiz.component';
import { FrontComponent } from './front/front.component';

const routes: Routes = [ { path: '', component: QuizComponent }, { path: 'front', component: FrontComponent }];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }